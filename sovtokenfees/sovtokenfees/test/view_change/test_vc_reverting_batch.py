import json

from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay
from sovtokenfees.test.helper import check_state, add_fees_request_with_address, \
    get_committed_hash_for_pool

from stp_core.loop.eventually import eventually

from plenum.test.helper import sdk_send_signed_requests, assertExp, sdk_sign_and_submit_req_obj

from plenum.test.view_change.helper import ensure_view_change

from plenum.test.test_node import ensureElectionsDone

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data

from plenum.common.startable import Mode

from plenum.common.constants import DOMAIN_LEDGER_ID


def test_revert_works_for_fees_after_view_change(looper, helpers,
                                                           nodeSetWithIntegratedTokenPlugin,
                                                           sdk_pool_handle,
                                                           sdk_wallet_trustee,
                                                           fees_set, address_main,
                                                           mint_tokens):
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

        committed_hash_before = get_committed_hash_for_pool(nodeSetWithIntegratedTokenPlugin, DOMAIN_LEDGER_ID)
        r = sdk_sign_and_submit_req_obj(looper, sdk_pool_handle, helpers.request._steward_wallet, request)

        for n in nodeSetWithIntegratedTokenPlugin:
            looper.run(eventually(check_state, n, False, retryWait=0.2, timeout=15))

        ensure_view_change(looper, nodeSetWithIntegratedTokenPlugin)

        for n in nodeSetWithIntegratedTokenPlugin:
            looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))

        ensureElectionsDone(looper=looper, nodes=nodeSetWithIntegratedTokenPlugin)
        committed_hash_after = get_committed_hash_for_pool(nodeSetWithIntegratedTokenPlugin, DOMAIN_LEDGER_ID)
        assert committed_hash_before == committed_hash_after

        ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)