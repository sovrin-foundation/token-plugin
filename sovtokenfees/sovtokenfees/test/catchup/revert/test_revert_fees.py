import functools

import pytest

from sovtoken.constants import XFER_PUBLIC, ADDRESS, AMOUNT, SEQNO, OUTPUTS, PAYMENT_ADDRESS
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import check_state, ensure_all_nodes_have_same_data, send_and_check_nym_with_fees

from indy_common.constants import NYM, ATTRIB, CONFIG_LEDGER_ID
from plenum.common.startable import Mode
from plenum.common.txn_util import get_seq_no
from plenum.test.delayers import cDelay, pDelay
from plenum.test.helper import assertExp
from plenum.test.stasher import delay_rules, delay_rules_without_processing
from plenum.test.test_node import ensureElectionsDone
from plenum.test.view_change.helper import ensure_view_change
from stp_core.loop.eventually import eventually

from plenum.common.constants import DOMAIN_LEDGER_ID


def get_len_preprepares(n):
    replica = n.master_replica
    return len(replica.sentPrePrepares if replica.isPrimary else replica.prePrepares)

def _get_ppseqno(n):
    return n.master_replica.last_prepared_certificate_in_view()[1]

def get_ppseqno_from_all_nodes(nodes):
    res = set()
    for n in nodes:
        res.add(_get_ppseqno(n))
    assert len(res) == 1
    return min(res)


def check_batch_ordered(old, nodes):
    for n in nodes:
        assert _get_ppseqno(n) == old + 1


def test_revert_during_view_change_all_nodes_xfer_with_fees(nodeSetWithIntegratedTokenPlugin, xfer_mint_tokens,
                               fees_set, helpers, looper, xfer_addresses):
    """
        Check that XFER and SET_FEES transaction will be written after view change when PREPARE quorum for it is reached
    """
    nodes = nodeSetWithIntegratedTokenPlugin
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    addr = xfer_addresses[0]
    utxo = helpers.general.get_utxo_addresses([addr])[0]

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

    utxos = helpers.general.get_utxo_addresses(xfer_addresses[1:])[0]
    assert utxos[0][PAYMENT_ADDRESS] == xfer_addresses[1]
    assert utxos[0][AMOUNT] == 998


def test_revert_during_view_change_all_nodes_nym_with_fees(nodeSetWithIntegratedTokenPlugin, xfer_mint_tokens,
                               fees_set, helpers, looper, xfer_addresses):
    """
        Check that NYM with FEES and SET_FEES transaction will be written after view change when PREPARE quorum for it is reached
    """
    nodes = nodeSetWithIntegratedTokenPlugin
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    addr = xfer_addresses[0]
    seq_no = get_seq_no(xfer_mint_tokens)

    _old_pp_seq_no = get_ppseqno_from_all_nodes(nodeSetWithIntegratedTokenPlugin)
    dledger_size_before = set([n.domainLedger.size for n in nodeSetWithIntegratedTokenPlugin]).pop()

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
    dledger_size_after = set([n.domainLedger.size for n in nodeSetWithIntegratedTokenPlugin]).pop()
    assert dledger_size_after > dledger_size_before
    for n in nodes:
        looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
    for n in nodes:
        looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))

    utxos = helpers.general.get_utxo_addresses([xfer_addresses[0]])[0]
    assert utxos[0][PAYMENT_ADDRESS] == xfer_addresses[0]
    assert utxos[0][AMOUNT] == 998


def test_revert_during_view_change_all_nodes_set_fees(tconf, nodeSetWithIntegratedTokenPlugin,
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


def test_revert_set_fees_and_view_change_all_nodes(nodeSetWithIntegratedTokenPlugin, xfer_mint_tokens, helpers, looper,
                                         xfer_addresses):
    """
        Send SET_FEES and init view change. Check that it is reverted and transaction passes with old fees
    """

    helpers.general.do_set_fees({NYM: 3})
    nodes = nodeSetWithIntegratedTokenPlugin
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]
    seq_no = get_seq_no(xfer_mint_tokens)
    _old_len_pprs = set([get_len_preprepares(n) for n in nodeSetWithIntegratedTokenPlugin])
    assert len(_old_len_pprs)
    _old_len_ppr = _old_len_pprs.pop()

    with delay_rules_without_processing(node_set, pDelay(), cDelay()):
        helpers.general.set_fees_without_waiting({NYM: 5})
        looper.run(eventually(functools.partial(check_batch_ordered, _old_len_ppr, nodeSetWithIntegratedTokenPlugin)))
        send_and_check_nym_with_fees(helpers,
                                     {FEES: {NYM: 5}},
                                     seq_no,
                                     looper,
                                     xfer_addresses,
                                     1000,
                                     check_reply=False)
        for n in nodeSetWithIntegratedTokenPlugin:
            n.master_replica.revert_unordered_batches()
            n.master_replica.requestQueues[DOMAIN_LEDGER_ID].clear()
            n.master_replica.requestQueues[CONFIG_LEDGER_ID].clear()
    ensure_all_nodes_have_same_data(looper, nodes)
    for n in nodes:
        looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
    for n in nodes:
        looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))

    send_and_check_nym_with_fees(helpers, {FEES: {NYM: 3}}, seq_no, looper, xfer_addresses, 1000)
