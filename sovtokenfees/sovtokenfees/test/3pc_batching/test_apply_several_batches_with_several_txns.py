import json

import pytest
from sovtoken.constants import TOKEN_LEDGER_ID
from sovtokenfees.test.helper import get_amount_from_token_txn, nyms_with_fees, \
    get_committed_txns_count_for_pool

from plenum.common.constants import NYM, DOMAIN_LEDGER_ID

from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies, assertExp

from plenum.test import waits

TXN_IN_BATCH = 3
NUM_BATCHES = 2


@pytest.fixture(scope="module")
def tconf(tconf):
    old_max_size = tconf.Max3PCBatchSize
    old_time = tconf.Max3PCBatchWait
    tconf.Max3PCBatchSize = TXN_IN_BATCH
    tconf.Max3PCBatchWait = 5
    yield tconf

    tconf.Max3PCBatchSize = old_max_size
    tconf.Max3PCBatchWait = old_time


def test_apply_several_batches_with_several_txns(looper, helpers,
                                                 nodeSetWithIntegratedTokenPlugin,
                                                 sdk_pool_handle,
                                                 fees_set, address_main, mint_tokens):
    current_amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1
    node_set = nodeSetWithIntegratedTokenPlugin
    all_reqs = nyms_with_fees(NUM_BATCHES * TXN_IN_BATCH,
                              helpers,
                              fees_set,
                              address_main,
                              current_amount,
                              init_seq_no=init_seq_no)
    domain_txns_before = get_committed_txns_count_for_pool(node_set, DOMAIN_LEDGER_ID)
    token_txns_before = get_committed_txns_count_for_pool(node_set, TOKEN_LEDGER_ID)
    r = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(req.as_dict) for req in all_reqs])
    looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
    sdk_get_and_check_replies(looper, r)
    domain_txns_after = get_committed_txns_count_for_pool(node_set, DOMAIN_LEDGER_ID)
    token_txns_after = get_committed_txns_count_for_pool(node_set, TOKEN_LEDGER_ID)

    assert domain_txns_after - domain_txns_before == NUM_BATCHES * TXN_IN_BATCH
    assert token_txns_after - token_txns_before == NUM_BATCHES * TXN_IN_BATCH
