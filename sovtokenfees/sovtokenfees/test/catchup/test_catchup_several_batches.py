import json

import pytest
from sovtokenfees.test.helper import get_amount_from_token_txn, nyms_with_fees

from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies, assertExp

from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay

from plenum.test import waits

from stp_core.loop.eventually import eventually

from plenum.common.startable import Mode

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data

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


def test_catchup_several_batches(looper, helpers,
                                 nodeSetWithIntegratedTokenPlugin,
                                 sdk_pool_handle,
                                 fees_set, address_main, mint_tokens):
    current_amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1
    node_set = nodeSetWithIntegratedTokenPlugin
    """
    Prepare NUM_BATCHES * TXN_IN_BATCH requests and 1 for checking pool functional
    """
    all_reqs = nyms_with_fees(NUM_BATCHES * TXN_IN_BATCH + 1,
                              helpers,
                              fees_set,
                              address_main,
                              current_amount,
                              init_seq_no=init_seq_no)
    reqs_to_catchup = all_reqs[:-1]
    req_for_check = all_reqs[-1]
    reverted_node = node_set[-1]
    with delay_rules(reverted_node.nodeIbStasher, cDelay()):

        len_batches_before = len(reverted_node.master_replica.batches)
        r = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(req.as_dict) for req in reqs_to_catchup])
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        len_batches_after = len(reverted_node.master_replica.batches)
        """
        Checks, that we have a 2 new batches
        """
        assert len_batches_after - len_batches_before == NUM_BATCHES
        sdk_get_and_check_replies(looper, r)
        reverted_node.start_catchup()
        looper.run(eventually(lambda: assertExp(reverted_node.mode == Mode.participating)))
    ensure_all_nodes_have_same_data(looper, node_set)

    r = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(req_for_check.as_dict)])
    sdk_get_and_check_replies(looper, r)
    ensure_all_nodes_have_same_data(looper, node_set)
