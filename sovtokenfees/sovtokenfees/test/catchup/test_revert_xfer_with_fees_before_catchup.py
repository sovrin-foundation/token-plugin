from sovtoken.constants import ADDRESS, SEQNO, AMOUNT, XFER_PUBLIC

from plenum.common.txn_util import get_seq_no

from plenum.test.stasher import delay_rules

from plenum.test.delayers import pDelay, cDelay

from plenum.test import waits
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
    seq_no = get_seq_no(xfer_mint_tokens)
    utxos = [{ADDRESS: address_giver, AMOUNT: 1000, SEQNO: seq_no}]
    inputs = [{ADDRESS: address_giver, SEQNO: seq_no}]
    outputs = [{ADDRESS: address_receiver, AMOUNT: 1000 - fees[XFER_PUBLIC]}]
    request = helpers.request.transfer(inputs, outputs)
    request = helpers.request.add_fees(
        request,
        utxos,
        fees[XFER_PUBLIC],
        change_address=address_giver
    )
    with delay_rules(node_stashers, cDelay(), pDelay()):
        helpers.sdk.send_request_objects([request])
        looper.runFor(waits.expectedPrePrepareTime(len(nodes)))
        for n in nodes:
            n.start_catchup()
        for n in nodes:
            looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
        for n in nodes:
            looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))
    ensure_all_nodes_have_same_data(looper, nodes)