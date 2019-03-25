import pytest
from sovtoken.constants import ADDRESS, SEQNO, AMOUNT, XFER_PUBLIC

from plenum.common.txn_util import get_seq_no

from plenum.test.stasher import delay_rules, delay_rules_without_processing

from plenum.test.delayers import pDelay, cDelay

from plenum.test import waits
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import check_state, get_amount_from_token_txn, nyms_with_fees

from stp_core.loop.eventually import eventually

from plenum.test.helper import assertExp

from plenum.common.startable import Mode

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data

from plenum.common.constants import NYM


@pytest.mark.skip(reason="ST-534")
def test_revert_xfer_and_other_txn_before_catchup(looper, helpers,
                                                  nodeSetWithIntegratedTokenPlugin,
                                                  sdk_pool_handle,
                                                  fees_set, fees,
                                                  xfer_mint_tokens, xfer_addresses):
    nodes = nodeSetWithIntegratedTokenPlugin
    node_stashers = [n.nodeIbStasher for n in nodes]
    current_amount = get_amount_from_token_txn(xfer_mint_tokens)
    init_seq_no = 1
    nym_with_fees = nyms_with_fees(1,
                                   helpers,
                                   fees_set,
                                   xfer_addresses[0],
                                   current_amount,
                                   init_seq_no=init_seq_no)[0]
    current_amount -= fees[NYM]
    [address_giver, address_receiver] = xfer_addresses
    utxos = [{ADDRESS: address_giver, AMOUNT: current_amount, SEQNO: init_seq_no + 1}]
    inputs = [{ADDRESS: address_giver, SEQNO: init_seq_no + 1}]
    outputs = [{ADDRESS: address_receiver, AMOUNT: current_amount - fees[XFER_PUBLIC]}]
    transfer_req = helpers.request.transfer(inputs, outputs)
    transfer_req = helpers.request.add_fees(
        transfer_req,
        utxos,
        fees[XFER_PUBLIC],
        change_address=address_giver
    )
    with delay_rules_without_processing(node_stashers, cDelay(), pDelay()):
        helpers.sdk.send_request_objects([nym_with_fees])
        helpers.sdk.send_request_objects([transfer_req])
        looper.runFor(waits.expectedPrePrepareTime(len(nodes)))
        for n in nodes:
            n.start_catchup()
        for n in nodes:
            looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
        for n in nodes:
            looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))
    ensure_all_nodes_have_same_data(looper, nodes)