import json

import pytest
from sovtoken import TOKEN_LEDGER_ID
from sovtokenfees.test.helper import get_amount_from_token_txn, nyms_with_fees

from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay

from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies, assertExp, \
    sdk_sign_and_submit_req_obj

from stp_core.loop.eventually import eventually

from plenum.common.startable import Mode


def get_last_committed_from_tracker(node):
    tracker = node.ledger_to_req_handler.get(TOKEN_LEDGER_ID).tracker
    return tracker.last_committed


@pytest.mark.skip(reason="tracker now in StaticFeeReqHandler")
def test_last_committed_after_catchup(looper, helpers,
                                      nodeSetWithIntegratedTokenPlugin,
                                      sdk_pool_handle,
                                      fees_set, address_main, mint_tokens):
    node_set = nodeSetWithIntegratedTokenPlugin
    reverted_node = node_set[-1]

    amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1
    request_1, request_2 = nyms_with_fees(2,
                                          helpers,
                                          fees_set,
                                          address_main,
                                          amount,
                                          init_seq_no=init_seq_no)
    reverted_last_committed = get_last_committed_from_tracker(reverted_node)
    not_reverted_last_committed = get_last_committed_from_tracker(node_set[-1])
    assert reverted_last_committed == not_reverted_last_committed
    with delay_rules(reverted_node.nodeIbStasher, cDelay()):
        """
        Send NYM with FEES and wait for reply. 
        """
        r = sdk_sign_and_submit_req_obj(looper, sdk_pool_handle, helpers.request._steward_wallet, request_1)
        sdk_get_and_check_replies(looper, [r])
        """
        Start catchup. Uncommitted batch for reverted_node should be rejected and it will get 
        NYM with FEES during catchup procedure. 
        """
        reverted_node.start_catchup()
        looper.run(eventually(lambda: assertExp(reverted_node.mode == Mode.participating)))
        assert get_last_committed_from_tracker(reverted_node) ==\
               get_last_committed_from_tracker(node_set[0])
