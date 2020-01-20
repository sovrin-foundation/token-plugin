import pytest
from sovtoken.constants import ADDRESS, SEQNO, AMOUNT

from plenum.common.txn_util import get_seq_no

from plenum.test.stasher import delay_rules, delay_rules_without_processing

from plenum.test.delayers import pDelay, cDelay

from plenum.test import waits
from sovtokenfees.test.constants import XFER_PUBLIC_FEES_ALIAS
from sovtokenfees.test.helper import check_state

from stp_core.loop.eventually import eventually

from plenum.test.helper import assertExp

from plenum.common.startable import Mode

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data


def test_revert_xfer_with_fees_before_catchup(looper, helpers,
                                              nodeSetWithIntegratedTokenPlugin,
                                              sdk_pool_handle,
                                              fees,
                                              xfer_mint_tokens, xfer_addresses):
    nodes = nodeSetWithIntegratedTokenPlugin
    node_stashers = [n.nodeIbStasher for n in nodes]
    helpers.general.do_set_fees(fees)
    [address_giver, address_receiver] = xfer_addresses
    inputs = helpers.general.get_utxo_addresses([address_giver])[0]
    outputs = [{ADDRESS: address_receiver, AMOUNT: 1000 - fees[XFER_PUBLIC_FEES_ALIAS]}]
    request = helpers.request.transfer(inputs, outputs)
    with delay_rules_without_processing(node_stashers, cDelay(), pDelay()):
        helpers.sdk.send_request_objects([request])
        looper.runFor(waits.expectedPrePrepareTime(len(nodes)))
        for n in nodes:
            n.start_catchup()
        # clear all request queues to not re-send the same reqs after catch-up
        for n in nodes:
            n.requests.clear()
            for r in n.replicas.values():
                for ledger_id, queue in r._ordering_service.requestQueues.items():
                    queue.clear()
        for n in nodes:
            looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
        for n in nodes:
            looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))
    ensure_all_nodes_have_same_data(looper, nodes)