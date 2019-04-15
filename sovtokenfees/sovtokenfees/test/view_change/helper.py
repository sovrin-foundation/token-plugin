from plenum.common.txn_util import get_seq_no

from plenum.test.stasher import delay_rules
from plenum.test.delayers import pDelay, cDelay
from plenum.test.view_change.helper import ensure_view_change
from plenum.test.test_node import ensureElectionsDone

from sovtokenfees.test.helper import ensure_all_nodes_have_same_data


def scenario_txns_during_view_change(
        looper,
        nodes,
        send_txns
):
    lagging_node = nodes[-1]
    rest_nodes = nodes[:-1]

    # Send XFER transaction
    send_txns()
    ensure_all_nodes_have_same_data(looper, nodes)

    # Lag one node (delay Prepare and  Commit messages for lagging_node)
    with delay_rules(
        lagging_node.nodeIbStasher, pDelay(), cDelay()
    ):
        # Send another transactions
        send_txns()
        ensure_all_nodes_have_same_data(looper, rest_nodes)

        # Send invalid transactions
        send_txns(invalid=True)
        ensure_all_nodes_have_same_data(looper, rest_nodes)

        # Initiate view change
        # Wait until view change is finished and check that needed transactions are written.
        ensure_view_change(looper, nodes)
        ensureElectionsDone(looper, nodes)

    # Reset delays
    # Make sure that all nodes have equal state
    # (expecting that lagging_node caught up missed ones)
    ensure_all_nodes_have_same_data(looper, nodes)
