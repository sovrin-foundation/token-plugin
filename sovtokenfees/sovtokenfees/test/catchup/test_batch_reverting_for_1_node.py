import json

from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay
from sovtokenfees.test.helper import check_state, add_fees_request_with_address

from stp_core.loop.eventually import eventually

from plenum.test.helper import sdk_send_signed_requests, assertExp, sdk_get_and_check_replies

from plenum.common.startable import Mode

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data



def test_revert_works_for_fees_before_catch_up_on_one_node(looper, helpers,
                                           nodeSetWithIntegratedTokenPlugin,
                                           sdk_pool_handle,
                                           sdk_wallet_trustee,
                                           fees_set, address_main, mint_tokens):
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    with delay_rules(node_set[0], cDelay()):
        request_check_health = helpers.request.nym()
        request_check_health = add_fees_request_with_address(
            helpers,
            fees_set,
            request_check_health,
            address_main
        )
        r = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(request_check_health.as_dict)])
        sdk_get_and_check_replies(looper, r)
        nodeSetWithIntegratedTokenPlugin[0].start_catchup()
    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)
