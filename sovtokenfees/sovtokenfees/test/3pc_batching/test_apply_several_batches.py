import json

import pytest

from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay
from sovtoken.constants import OUTPUTS, AMOUNT, ADDRESS, TOKEN_LEDGER_ID
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import get_amount_from_token_txn, check_uncommitted_txn, add_fees_request_with_address, \
    get_committed_txns_count_for_pool, nyms_with_fees

from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies

from plenum.common.constants import DATA, TXN_TYPE

from plenum.common.types import f

from stp_core.loop.eventually import eventually


@pytest.fixture(scope="module")
def tconf(tconf):
    old_max_size = tconf.Max3PCBatchSize
    tconf.Max3PCBatchSize = 1
    yield tconf

    tconf.Max3PCBatchSize = old_max_size


def test_apply_several_batches(looper, helpers,
                               nodeSetWithIntegratedTokenPlugin,
                               sdk_pool_handle,
                               fees_set, address_main, mint_tokens):
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]
    amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1
    request1, request2 = nyms_with_fees(2,
                                        helpers,
                                        fees_set,
                                        address_main,
                                        amount,
                                        init_seq_no=init_seq_no)
    expected_txns_length = 2
    txns_count_before = get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin, TOKEN_LEDGER_ID)
    with delay_rules(node_set, cDelay()):
        r1 = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(request1.as_dict)])
        r2 = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(request2.as_dict)])
        for n in nodeSetWithIntegratedTokenPlugin:
            looper.run(eventually(check_uncommitted_txn, n, expected_txns_length, TOKEN_LEDGER_ID, retryWait=0.2, timeout=15))

    sdk_get_and_check_replies(looper, r1)
    sdk_get_and_check_replies(looper, r2)
    txns_count_after = get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin, TOKEN_LEDGER_ID)
    assert txns_count_after - txns_count_before == expected_txns_length
