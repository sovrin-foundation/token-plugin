import functools

import pytest

from sovtoken.constants import XFER_PUBLIC, ADDRESS, AMOUNT, SEQNO, OUTPUTS
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import check_state, ensure_all_nodes_have_same_data, send_and_check_nym_with_fees

from indy_common.constants import NYM, ATTRIB
from plenum.common.startable import Mode
from plenum.common.txn_util import get_seq_no
from plenum.test.delayers import cDelay
from plenum.test.helper import assertExp
from plenum.test.stasher import delay_rules
from plenum.test.test_node import ensureElectionsDone
from plenum.test.view_change.helper import ensure_view_change
from stp_core.loop.eventually import eventually


@pytest.fixture(scope="module")
def tconf(tconf):
    old_max_size = tconf.Max3PCBatchSize
    old_time = tconf.Max3PCBatchWait
    tconf.Max3PCBatchSize = 2
    tconf.Max3PCBatchWait = 5
    yield tconf

    tconf.Max3PCBatchSize = old_max_size
    tconf.Max3PCBatchWait = old_time


def get_ppseqno_from_node(n):
    return n.master_replica.last_prepared_certificate_in_view()[1]


def get_ppseqno_from_all_nodes(nodes):
    res = set()
    for n in nodes:
        res.add(get_ppseqno_from_node(n))
    assert len(res) == 1
    return min(res)


def check_batch_ordered(old, nodes):
    for n in nodes:
        assert get_ppseqno_from_node(n) == old + 1


def test_revert_fees_with_xfer(nodeSetWithIntegratedTokenPlugin, xfer_mint_tokens,
                               fees_set, helpers, looper, xfer_addresses):
    """
        Check that XFER transaction will be written after view change when PREPARE quorum for it is reached
    """
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

    _old_pp_seq_no = get_ppseqno_from_all_nodes(nodeSetWithIntegratedTokenPlugin)

    with delay_rules(node_set, cDelay()):
        # should be changed for auth rule
        helpers.general.set_fees_without_waiting({XFER_PUBLIC: 2})
        looper.run(eventually(functools.partial(check_batch_ordered, _old_pp_seq_no, nodeSetWithIntegratedTokenPlugin)))
        helpers.general.transfer_without_waiting(utxo, outputs)
        looper.run(
            eventually(functools.partial(check_batch_ordered, _old_pp_seq_no + 1, nodeSetWithIntegratedTokenPlugin)))
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


def test_revert_during_view_change_all_nodes_nym_with_fees(nodeSetWithIntegratedTokenPlugin, xfer_mint_tokens,
                               fees_set, helpers, looper, xfer_addresses):
    """
        Check that NYM with FEES transaction will be written after view change when PREPARE quorum for it is reached
    """
    nodes = nodeSetWithIntegratedTokenPlugin
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    addr = xfer_addresses[0]
    seq_no = get_seq_no(xfer_mint_tokens)

    _old_pp_seq_no = get_ppseqno_from_all_nodes(nodeSetWithIntegratedTokenPlugin)

    with delay_rules(node_set, cDelay()):
        # should be changed for auth rule
        helpers.general.set_fees_without_waiting({NYM: 2})
        looper.run(eventually(functools.partial(check_batch_ordered, _old_pp_seq_no, nodeSetWithIntegratedTokenPlugin)))
        send_and_check_nym_with_fees(helpers, {FEES: {NYM: 2}}, seq_no, looper, xfer_addresses, 1000, check_reply=False)
        looper.run(
            eventually(functools.partial(check_batch_ordered, _old_pp_seq_no + 1, nodeSetWithIntegratedTokenPlugin)))
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


def test_view_change_with_set_fees(tconf, nodeSetWithIntegratedTokenPlugin,
                                    fees_set, helpers, looper):
    """
        Check that SET_FEES transaction will be written after view change when PREPARE quorum for it is reached
    """
    nodes = nodeSetWithIntegratedTokenPlugin
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    _old_pp_seq_no = get_ppseqno_from_all_nodes(nodeSetWithIntegratedTokenPlugin)
    helpers.general.set_fees_without_waiting({ATTRIB: 3})

    assert _old_pp_seq_no == get_ppseqno_from_all_nodes(nodeSetWithIntegratedTokenPlugin)

    with delay_rules(node_set, cDelay()):
        # should be changed for auth rule
        helpers.general.set_fees_without_waiting({ATTRIB: 4})
        looper.run(eventually(functools.partial(check_batch_ordered, _old_pp_seq_no, nodeSetWithIntegratedTokenPlugin)))
        ensure_view_change(looper, nodes)

    ensureElectionsDone(looper=looper, nodes=nodes)
    ensure_all_nodes_have_same_data(looper, nodes)
    for n in nodes:
        looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
    for n in nodes:
        looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))

    fees = helpers.general.do_get_fees()
    assert fees[FEES][ATTRIB] == 4
