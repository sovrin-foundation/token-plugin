import json

from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay
from sovtokenfees.test.helper import add_fees_request_with_address, check_state

from stp_core.loop.eventually import eventually

from plenum.test.helper import sdk_send_signed_requests, assertExp, sdk_sign_and_submit_req_obj

from plenum.common.startable import Mode

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data


def test_revert_works_for_fees_before_catch_up_on_all_nodes(looper, helpers,
                                                        nodeSetWithIntegratedTokenPlugin,
                                                        sdk_pool_handle,
                                                        sdk_wallet_trustee,
                                                        fees_set, address_main, mint_tokens):
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    with delay_rules(node_set, cDelay()):
        request = helpers.request.nym()

        request = add_fees_request_with_address(
            helpers,
            fees_set,
            request,
            address_main
        )
        for n in nodeSetWithIntegratedTokenPlugin:
            looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))

        sdk_sign_and_submit_req_obj(looper, sdk_pool_handle, helpers.request._steward_wallet, request)

        for n in nodeSetWithIntegratedTokenPlugin:
            looper.run(eventually(check_state, n, False, retryWait=0.2, timeout=15))

        for n in nodeSetWithIntegratedTokenPlugin:
            n.start_catchup()

        for n in nodeSetWithIntegratedTokenPlugin:
            looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))

        for n in nodeSetWithIntegratedTokenPlugin:
            looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))

    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)