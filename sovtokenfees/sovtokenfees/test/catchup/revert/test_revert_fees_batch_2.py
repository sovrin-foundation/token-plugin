import functools

import pytest
from sovtokenfees.constants import FEES
from sovtokenfees.test.catchup.revert.test_revert_fees import get_ppseqno_from_all_nodes, check_batch_ordered
from sovtokenfees.test.constants import ATTRIB_FEES_ALIAS
from sovtokenfees.test.helper import ensure_all_nodes_have_same_data, check_state

from indy_common.constants import ATTRIB
from plenum.common.startable import Mode
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
    tconf.Max3PCBatchWait = 1000
    yield tconf

    tconf.Max3PCBatchSize = old_max_size
    tconf.Max3PCBatchWait = old_time


def test_revert_during_view_change_all_nodes_set_fees(tconf, nodeSetWithIntegratedTokenPlugin,
                                    fees_set_with_batch, helpers, looper):
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
