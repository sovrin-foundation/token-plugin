import functools

import pytest

from sovtoken.constants import ADDRESS, AMOUNT, PAYMENT_ADDRESS
from sovtokenfees.constants import FEES
from sovtokenfees.test.constants import NYM_FEES_ALIAS, XFER_PUBLIC_FEES_ALIAS, ATTRIB_FEES_ALIAS
from sovtokenfees.test.helper import check_state, ensure_all_nodes_have_same_data, send_and_check_nym_with_fees

from indy_common.constants import NYM, ATTRIB, CONFIG_LEDGER_ID
from plenum.common.startable import Mode
from plenum.common.txn_util import get_seq_no
from plenum.test.delayers import cDelay, pDelay
from plenum.test.helper import assertExp, sdk_get_and_check_replies
from plenum.test.stasher import delay_rules, delay_rules_without_processing
from plenum.test.test_node import ensureElectionsDone
from plenum.test.view_change.helper import ensure_view_change
from stp_core.loop.eventually import eventually

from plenum.common.constants import DOMAIN_LEDGER_ID


def _get_ppseqno(n):
    return n.master_replica._ordering_service.l_last_prepared_certificate_in_view()[1]

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
        helpers.general.set_fees_without_waiting({XFER_PUBLIC_FEES_ALIAS: 2})
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


def test_revert_during_view_change_all_nodes_set_fees(tconf, nodeSetWithIntegratedTokenPlugin,
                                    fees_set, helpers, looper):
    """
        Check that SET_FEES transaction will be written after view change when PREPARE quorum for it is reached
    """
    nodes = nodeSetWithIntegratedTokenPlugin
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    _old_pp_seq_no = get_ppseqno_from_all_nodes(nodeSetWithIntegratedTokenPlugin)
    helpers.general.set_fees_without_waiting({ATTRIB_FEES_ALIAS: 3})

    assert _old_pp_seq_no == get_ppseqno_from_all_nodes(nodeSetWithIntegratedTokenPlugin)

    with delay_rules(node_set, cDelay()):
        # should be changed for auth rule
        helpers.general.set_fees_without_waiting({ATTRIB_FEES_ALIAS: 4})
        looper.run(eventually(functools.partial(check_batch_ordered, _old_pp_seq_no, nodeSetWithIntegratedTokenPlugin)))
        ensure_view_change(looper, nodes)

    ensureElectionsDone(looper=looper, nodes=nodes)
    ensure_all_nodes_have_same_data(looper, nodes)
    for n in nodes:
        looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
    for n in nodes:
        looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))

    fees = helpers.general.do_get_fees()
    assert fees[FEES][ATTRIB_FEES_ALIAS] == 4


def test_revert_set_fees_and_view_change_all_nodes(nodeSetWithIntegratedTokenPlugin, xfer_mint_tokens, helpers, looper,
                                         xfer_addresses):
    """
        Send SET_FEES and init view change. Check that it is reverted and transaction passes with old fees
    """

    def _get_len_preprepares(n):
        replica = n.master_replica
        return len(replica._ordering_service.sentPrePrepares if replica.isPrimary else replica._ordering_service.prePrepares)

    def _check_len_pprs(old_pprs_len):
        _len_pprs = set([_get_len_preprepares(n) for n in nodeSetWithIntegratedTokenPlugin])
        _len_ppr = _len_pprs.pop()
        assert old_pprs_len + 1 == _len_ppr

    helpers.general.do_set_fees({NYM_FEES_ALIAS: 3})
    nodes = nodeSetWithIntegratedTokenPlugin
    node_stashers = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]
    seq_no = get_seq_no(xfer_mint_tokens)
    _old_len_pprs = set([_get_len_preprepares(n) for n in nodeSetWithIntegratedTokenPlugin])
    assert len(_old_len_pprs)
    _old_len_ppr = _old_len_pprs.pop()

    with delay_rules_without_processing(node_stashers, cDelay()):
        helpers.general.set_fees_without_waiting({NYM_FEES_ALIAS: 5})
        looper.run(eventually(functools.partial(_check_len_pprs, _old_len_ppr)))
        send_and_check_nym_with_fees(helpers,
                                     {FEES: {NYM_FEES_ALIAS: 5}},
                                     seq_no,
                                     looper,
                                     xfer_addresses,
                                     1000,
                                     check_reply=False)
        for n in nodeSetWithIntegratedTokenPlugin:
            n.start_catchup()
        for n in nodes:
            looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
    ensure_all_nodes_have_same_data(looper, nodes)
    send_and_check_nym_with_fees(helpers,
                                 {FEES: {NYM_FEES_ALIAS: 3}},
                                 seq_no,
                                 looper,
                                 xfer_addresses,
                                 1000,
                                 check_reply=False)
    ensure_all_nodes_have_same_data(looper, nodes)
