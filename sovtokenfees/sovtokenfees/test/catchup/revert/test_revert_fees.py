from threading import Thread

import pytest
from sovtoken.constants import XFER_PUBLIC, ADDRESS, AMOUNT, SEQNO, OUTPUTS
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import check_state, ensure_all_nodes_have_same_data, send_and_check_nym_with_fees

from indy_common.constants import NYM
from plenum.common.startable import Mode
from plenum.common.txn_util import get_seq_no
from plenum.test.delayers import cDelay
from plenum.test import waits
from plenum.test.helper import assertExp
from plenum.test.stasher import delay_rules
from plenum.test.test_node import ensureElectionsDone
from plenum.test.view_change.helper import ensure_view_change
from stp_core.loop.eventually import eventually


def test_revert_fees_with_xfer(nodeSetWithIntegratedTokenPlugin, xfer_mint_tokens,
                               fees_set, helpers, looper, xfer_addresses):
    nodes = nodeSetWithIntegratedTokenPlugin
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    addr = xfer_addresses[0]
    seq_no = get_seq_no(xfer_mint_tokens)
    utxo = [{
        ADDRESS: addr,
        SEQNO: seq_no
    }]

    outputs = [{
        ADDRESS: xfer_addresses[1],
        AMOUNT: 998
    }]

    with delay_rules(node_set, cDelay()):
        # should be changed for auth rule
        helpers.general.set_fees_without_waiting({XFER_PUBLIC: 2})
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        helpers.general.transfer_without_waiting(utxo, outputs)
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        ensure_view_change(looper, nodes)

    ensureElectionsDone(looper=looper, nodes=nodes)
    ensure_all_nodes_have_same_data(looper, nodes)
    for n in nodes:
        looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
    for n in nodes:
        looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))

    utxos = helpers.general.do_get_utxo(xfer_addresses[1])
    assert utxos[OUTPUTS][0][ADDRESS] == xfer_addresses[1]
    assert utxos[OUTPUTS][0][AMOUNT] == 998
    assert utxos[OUTPUTS][0][SEQNO] == seq_no+1


def test_revert_fees_with_nym(nodeSetWithIntegratedTokenPlugin, xfer_mint_tokens,
                               fees_set, helpers, looper, xfer_addresses):
    nodes = nodeSetWithIntegratedTokenPlugin
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    addr = xfer_addresses[0]
    seq_no = get_seq_no(xfer_mint_tokens)

    with delay_rules(node_set, cDelay()):
        # should be changed for auth rule
        helpers.general.set_fees_without_waiting({NYM: 2})
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        send_and_check_nym_with_fees(helpers, {FEES: {NYM: 2}}, seq_no, looper, xfer_addresses, 1000, check_reply=False)
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        ensure_view_change(looper, nodes)

    ensureElectionsDone(looper=looper, nodes=nodes)
    ensure_all_nodes_have_same_data(looper, nodes)
    for n in nodes:
        looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
    for n in nodes:
        looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))

    utxos = helpers.general.do_get_utxo(xfer_addresses[0])
    assert utxos[OUTPUTS][0][ADDRESS] == xfer_addresses[0]
    assert utxos[OUTPUTS][0][AMOUNT] == 998
    assert utxos[OUTPUTS][0][SEQNO] == seq_no + 1
