import json

from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay
from sovtoken import TOKEN_LEDGER_ID
from sovtokenfees.test.helper import get_amount_from_token_txn, \
    nyms_with_fees, get_committed_txn_root_for_pool, check_state

from stp_core.loop.eventually import eventually

from plenum.test.helper import sdk_send_signed_requests, assertExp, sdk_get_and_check_replies, \
    sdk_sign_and_submit_req_obj

from plenum.common.startable import Mode

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data


def test_revert_works_for_fees_before_catch_up_on_one_node(looper, helpers,
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
    c_ledger_root_before = get_committed_txn_root_for_pool([reverted_node], TOKEN_LEDGER_ID)
    with delay_rules(reverted_node.nodeIbStasher, cDelay()):
        """
        Send NYM with FEES and wait for reply. All of nodes, except reverted_node will order them 
        """
        r = sdk_sign_and_submit_req_obj(looper, sdk_pool_handle, helpers.request._steward_wallet, request_1)
        sdk_get_and_check_replies(looper, [r])
        check_state(reverted_node, is_equal=False)
        c_ledger_root_for_other = get_committed_txn_root_for_pool(node_set[:-1], TOKEN_LEDGER_ID)
        """
        Start catchup. Uncommitted batch for reverted_node should be rejected and it will get 
        NYM with FEES during catchup procedure. 
        """
        reverted_node.start_catchup()
        looper.run(eventually(lambda: assertExp(reverted_node.mode == Mode.participating)))
        check_state(reverted_node, is_equal=True)
        """
        Check, that committed txn root was changed and it's the same as for others
        """
        c_ledger_root_after = get_committed_txn_root_for_pool([reverted_node], TOKEN_LEDGER_ID)
        assert c_ledger_root_after != c_ledger_root_before
        assert c_ledger_root_after == c_ledger_root_for_other
    ensure_all_nodes_have_same_data(looper, node_set)
    c_ledger_root_before = get_committed_txn_root_for_pool(node_set, TOKEN_LEDGER_ID)
    """
    Send another NYM with FEES and check, that committed ledger's root was changed
    """
    r = sdk_sign_and_submit_req_obj(looper, sdk_pool_handle, helpers.request._steward_wallet, request_2)
    sdk_get_and_check_replies(looper, [r])
    c_ledger_root_after = get_committed_txn_root_for_pool(node_set, TOKEN_LEDGER_ID)
    assert c_ledger_root_after != c_ledger_root_before
    ensure_all_nodes_have_same_data(looper, node_set)
    for n in node_set:
        check_state(n, is_equal=True)
