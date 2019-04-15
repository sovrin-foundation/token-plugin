import pytest

from plenum.common.constants import DOMAIN_LEDGER_ID
from plenum.common.txn_util import get_seq_no

from plenum.test.stasher import delay_rules
from plenum.test.delayers import cr_delay
from plenum.test.test_node import checkNodesConnected
from plenum.test.pool_transactions.helper import \
    disconnect_node_and_ensure_disconnected

from indy_common.constants import NYM
from indy_node.test.helper import start_stopped_node

from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_transfer, \
    send_and_check_nym_with_fees, ensure_all_nodes_have_same_data

# no fees for XFER_PUBLIC
TXN_FEES = {
    NYM: 4
}


def send_txns(helpers, fees_set, fees, looper, xfer_addresses, current_amount, seq_no):
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, xfer_addresses,
                                                             current_amount)
    return send_and_check_transfer(helpers, xfer_addresses, fees, looper, current_amount, seq_no)


def test_revert_xfer_and_other_txn_before_catchup(
        looper, helpers, tconf, tdir, allPluginsPath,
        nodeSetWithIntegratedTokenPlugin,
        fees_set, fees,
        xfer_mint_tokens, xfer_addresses,
        do_post_node_creation
):
    nodes = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(xfer_mint_tokens)
    seq_no = get_seq_no(xfer_mint_tokens)
    lagging_node = nodes[-1]
    rest_nodes = nodes[:-1]

    # Stop NodeX
    lagging_node.cleanupOnStopping = False
    disconnect_node_and_ensure_disconnected(looper,
                                            nodes,
                                            lagging_node.name,
                                            stopNode=True)
    looper.removeProdable(name=lagging_node.name)

    # Send 1 XFER txn (no fees) and make sure it’s written
    # Send 1 NYM+FEEs txn and make sure it’s written
    current_amount, seq_no, _ = send_txns(
        helpers, fees_set, fees, looper,
        xfer_addresses, current_amount, seq_no
    )
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
        # Send 1 XFER txn (no fees) and make sure it’s ordered by all Nodes except NodeX
        # Send 1 NYM+FEEs txn and make sure it’s ordered by all Nodes except NodeX
        current_amount, seq_no, _ = send_txns(
            helpers, fees_set, fees, looper,
            xfer_addresses, current_amount, seq_no
        )
        ensure_all_nodes_have_same_data(looper, rest_nodes)

    # Reset delays
    # Make sure that all nodes have equal state
    ensure_all_nodes_have_same_data(looper, nodes)

    # Send 1 XFER txn (no fees) and make sure it’s written
    # Send 1 NYM+FEEs txn and make sure it’s written
    # Make sure that all nodes have equal state
    current_amount, seq_no, _ = send_txns(
        helpers, fees_set, fees, looper,
        xfer_addresses, current_amount, seq_no
    )
    ensure_all_nodes_have_same_data(looper, nodes)
