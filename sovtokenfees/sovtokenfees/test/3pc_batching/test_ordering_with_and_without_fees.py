import json

import pytest
from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import ADDRESS, AMOUNT
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import add_fees_request_with_address, get_committed_txns_count_for_pool, sdk_send_new_nym, \
    get_amount_from_token_txn

from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data

from plenum.test import waits

from plenum.common.constants import DOMAIN_LEDGER_ID, TXN_TYPE

from plenum.common.types import f


@pytest.fixture(scope="module")
def tconf(tconf):
    old_max_size = tconf.Max3PCBatchSize
    tconf.Max3PCBatchSize = 1
    yield tconf

    tconf.Max3PCBatchSize = old_max_size


def test_ordering_with_fees_and_without_fees(looper, helpers,
                                             nodeSetWithIntegratedTokenPlugin,
                                             sdk_pool_handle,
                                             sdk_wallet_steward,
                                             fees_set, address_main, mint_tokens,
                                             fees):
    node_set = nodeSetWithIntegratedTokenPlugin
    node_stashers = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    committed_tokens_before = get_committed_txns_count_for_pool(node_set, TOKEN_LEDGER_ID)
    committed_domain_before = get_committed_txns_count_for_pool(node_set, DOMAIN_LEDGER_ID)
    """
    We will try to send a 1 NYM txn with fees and 1 NYM without fees and 1 with fees
    In that case we expect, that we will have 3 domain txn and 2 token txn in ledgers
    """
    expected_domain_txns_count = 3
    expected_token_txns_count = 2
    with delay_rules(node_stashers, cDelay()):
        request_1 = helpers.request.nym()
        request_2 = helpers.request.nym()
        request_1 = add_fees_request_with_address(
            helpers,
            fees_set,
            request_1,
            address_main
        )
        fee_amount = fees_set[FEES][request_1.operation[TXN_TYPE]]
        amount = get_amount_from_token_txn(mint_tokens)
        init_seq_no = 1
        utxos = [{ADDRESS: address_main,
                  AMOUNT: amount - fee_amount,
                  f.SEQ_NO.nm: init_seq_no + 1}]
        request_2 = add_fees_request_with_address(
            helpers,
            fees_set,
            request_2,
            address_main,
            utxos=utxos)
        """
        Sending 1 NYM txn with fees
        """
        r_with_1 = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(request_1.as_dict)])
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        """
        Unset fees for pool
        """
        helpers.node.reset_fees()
        """
        Sending 1 NYM txn without fees
        """
        r_without = sdk_send_new_nym(looper, sdk_pool_handle, sdk_wallet_steward)
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        """
        Set fees for pool
        """
        r_set_fees = helpers.general.set_fees_without_waiting(fees)
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        """
        Send another NYM txn with fees
        """
        r_with_2 = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(request_2.as_dict)])
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
    """
    Reset delays and check, that all txns was ordered successfully
    """
    sdk_get_and_check_replies(looper, r_with_1)
    sdk_get_and_check_replies(looper, r_without)
    sdk_get_and_check_replies(looper, r_set_fees)
    sdk_get_and_check_replies(looper, r_with_2)

    committed_tokens_after = get_committed_txns_count_for_pool(node_set, TOKEN_LEDGER_ID)
    committed_domain_after = get_committed_txns_count_for_pool(node_set, DOMAIN_LEDGER_ID)
    assert committed_domain_after - committed_domain_before == expected_domain_txns_count
    assert committed_tokens_after - committed_tokens_before == expected_token_txns_count

    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)
