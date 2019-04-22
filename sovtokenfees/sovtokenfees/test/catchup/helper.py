from plenum.common.constants import DOMAIN_LEDGER_ID

from plenum.test.stasher import delay_rules
from plenum.test.delayers import cr_delay
from plenum.test.test_node import checkNodesConnected
from plenum.test.pool_transactions.helper import \
    disconnect_node_and_ensure_disconnected

from indy_node.test.helper import start_stopped_node

from sovtokenfees.test.helper import ensure_all_nodes_have_same_data


def scenario_txns_during_catchup(
        looper, tconf, tdir, allPluginsPath, do_post_node_creation,
        nodes,
        send_txns
):
    lagging_node = nodes[-1]
    rest_nodes = nodes[:-1]

    # Stop NodeX
    lagging_node.cleanupOnStopping = False
    disconnect_node_and_ensure_disconnected(looper,
                                            nodes,
                                            lagging_node.name,
                                            stopNode=True)
    looper.removeProdable(name=lagging_node.name)

    # Send transactions
    send_txns()
    ensure_all_nodes_have_same_data(looper, rest_nodes)

    # Start NodeX
    lagging_node = start_stopped_node(
        lagging_node,
        looper,
        tconf,
        tdir,
        allPluginsPath,
        start=False,
    )
    do_post_node_creation(lagging_node)
    nodes[-1] = lagging_node

    # Delay CathupRep for DOMAIN ledger for NodeX
    with delay_rules(
        lagging_node.nodeIbStasher, cr_delay(ledger_filter=DOMAIN_LEDGER_ID)
    ):
        # allow started node to receive looper events
        looper.add(lagging_node)
        # ensure it connected to others
        looper.run(checkNodesConnected(nodes))
        # Send transactions
        send_txns()
        ensure_all_nodes_have_same_data(looper, rest_nodes)

    # Reset delays
    # Make sure that all nodes have equal state
    ensure_all_nodes_have_same_data(looper, nodes)

    # Send transactions
    send_txns()
    ensure_all_nodes_have_same_data(looper, rest_nodes)
