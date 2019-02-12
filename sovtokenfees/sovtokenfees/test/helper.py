from plenum.common.constants import DOMAIN_LEDGER_ID, DATA, TXN_TYPE
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import OUTPUTS, AMOUNT
from sovtokenfees.constants import FEES


def check_state(n, is_equal=False):
    assert (n.getLedgerRootHash(DOMAIN_LEDGER_ID, isCommitted=False) == n.getLedgerRootHash(DOMAIN_LEDGER_ID,
                                                                                            isCommitted=True)) == is_equal

    assert (n.getLedgerRootHash(TOKEN_LEDGER_ID, isCommitted=False) ==
            n.getLedgerRootHash(TOKEN_LEDGER_ID, isCommitted=True)) == is_equal

    assert (n.getState(DOMAIN_LEDGER_ID).headHash ==
            n.getState(DOMAIN_LEDGER_ID).committedHeadHash) == is_equal

    assert (n.getState(TOKEN_LEDGER_ID).headHash ==
            n.getState(TOKEN_LEDGER_ID).committedHeadHash) == is_equal


def get_amount_from_token_txn(token_txn):
    return token_txn['txn'][DATA][OUTPUTS][0][AMOUNT]


def check_uncommitted_txn(node, expected_length, ledger_id):
    assert len(node.getLedger(ledger_id).uncommittedTxns) == expected_length


def add_fees_request_with_address(helpers, fees_set, request, address, utxos=None):
    utxos = utxos if utxos else helpers.general.get_utxo_addresses([address])[0]
    fee_amount = fees_set[FEES][request.operation[TXN_TYPE]]
    helpers.request.add_fees(
        request,
        utxos,
        fee_amount,
        change_address=address
    )
    return request


def pay_fees(helpers, fees_set, address_main):
    request = helpers.request.nym()

    request = add_fees_request_with_address(
        helpers,
        fees_set,
        request,
        address_main
    )

    responses = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(responses)
    return result


def get_committed_txns_count_for_pool(node_set, ledger_id):
    txns_counts = set([n.getLedger(ledger_id).size for n in node_set])
    assert len(txns_counts) == 1
    return txns_counts.pop()


def get_uncommitted_txns_count_for_pool(node_set, ledger_id):
    txns_counts = set([n.getLedger(ledger_id).uncommitted_size for n in node_set])
    assert len(txns_counts) == 1
    return txns_counts.pop()


def get_head_hash_for_pool(node_set, ledger_id):
    head_hashes = set([n.getState(ledger_id).headHash for n in node_set])
    assert len(head_hashes) == 1
    return head_hashes.pop()
