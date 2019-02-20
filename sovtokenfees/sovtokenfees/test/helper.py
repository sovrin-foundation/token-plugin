import json

from plenum.common.constants import DOMAIN_LEDGER_ID, DATA, TXN_TYPE, NYM
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import OUTPUTS, AMOUNT, ADDRESS
from sovtokenfees.constants import FEES

from plenum.common.util import randomString

from plenum.test.pool_transactions.helper import prepare_nym_request, sdk_sign_and_send_prepared_request

from plenum.test.helper import sdk_json_to_request_object, sdk_sign_request_objects, sdk_send_signed_requests

from plenum.common.types import f


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


def get_committed_hash_for_pool(node_set, ledger_id):
    head_hashes = set([n.getState(ledger_id).committedHeadHash for n in node_set])
    assert len(head_hashes) == 1
    return head_hashes.pop()


def get_committed_txn_root_for_pool(node_set, ledger_id):
    hashes = set([n.getLedgerRootHash(ledger_id, isCommitted=True) for n in node_set])
    assert len(hashes) == 1
    return hashes.pop()


def get_uncommitted_txn_root_for_pool(node_set, ledger_id):
    hashes = set([n.getLedgerRootHash(ledger_id, isCommitted=False) for n in node_set])
    assert len(hashes) == 1
    return hashes.pop()


def sdk_send_new_nym(looper, sdk_pool_handle, creators_wallet,
                     alias=None, role=None, seed=None,
                     dest=None, verkey=None,skipverkey=False):
    seed = seed or randomString(32)
    alias = alias or randomString(5)
    wh, _ = creators_wallet

    # filling nym request and getting steward did
    # if role == None, we are adding client
    nym_request, new_did = looper.loop.run_until_complete(
        prepare_nym_request(creators_wallet, seed,
                            alias, role, dest, verkey, skipverkey))

    # sending request using 'sdk_' functions
    signed_reqs = sdk_sign_request_objects(looper, creators_wallet,
                                           [sdk_json_to_request_object(
                                               json.loads(nym_request))])
    request_couple = sdk_send_signed_requests(sdk_pool_handle, signed_reqs)
    return request_couple


def nyms_with_fees(req_count,
                   helpers,
                   fees_set,
                   address_main,
                   all_amount,
                   init_seq_no):
    amount = all_amount
    seq_no = init_seq_no
    fee_amount = fees_set[FEES][NYM]
    reqs = []
    for i in range(req_count):
        req = helpers.request.nym()
        utxos = [{ADDRESS: address_main,
                  AMOUNT: amount,
                  f.SEQ_NO.nm: seq_no}]
        reqs.append(add_fees_request_with_address(helpers,
                                                  fees_set,
                                                  req,
                                                  address_main,
                                                  utxos=utxos))
        seq_no += 1
        amount -= fee_amount
    return reqs
