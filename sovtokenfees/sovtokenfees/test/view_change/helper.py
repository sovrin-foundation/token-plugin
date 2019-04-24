import pytest

from plenum.common.exceptions import RequestRejectedException

from plenum.test.stasher import delay_rules
from plenum.test.delayers import pDelay, cDelay
from plenum.test.view_change.helper import ensure_view_change
from plenum.test.test_node import ensureElectionsDone

from sovtokenfees.test.helper import ensure_all_nodes_have_same_data


def scenario_txns_during_view_change(
        looper,
        nodes,
        curr_utxo,
        send_txns,
        send_txns_invalid=None
):
    lagging_node = nodes[-1]
    rest_nodes = nodes[:-1]

    def send_txns_invalid_default():
        curr_utxo['amount'] += 1
        with pytest.raises(RequestRejectedException, match='Insufficient funds'):
            send_txns()
        curr_utxo['amount'] -= 1

    # Send transactions
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
        (send_txns_invalid or send_txns_invalid_default)()
        ensure_all_nodes_have_same_data(looper, rest_nodes)

        # Initiate view change
        # Wait until view change is finished and check that needed transactions are written.
        ensure_view_change(looper, nodes)
        ensureElectionsDone(looper, nodes)

    # Reset delays
    # Make sure that all nodes have equal state
    # (expecting that lagging_node caught up missed ones)
    ensure_all_nodes_have_same_data(looper, nodes)

    # make sure the poll is functional
    send_txns()
    ensure_all_nodes_have_same_data(looper, nodes)


def scenario_txns_during_view_change_new(
        looper,
        helpers,
        nodes,
        io_addresses,
        send_txns,
        send_txns_invalid=None
):
    lagging_node = nodes[-1]
    rest_nodes = nodes[:-1]

    def send_txns_invalid_default():
        # TODO non-public API is used
        addr = helpers.wallet.address_map[io_addresses[0][0]]
        seq_no = list(addr.outputs[0])[0]
        assert addr.outputs[0][seq_no] > 0

        # de-sync client-server utxos states
        addr.outputs[0][seq_no] += 1
        with pytest.raises(RequestRejectedException, match='Insufficient funds'):
            send_txns()
        # sync back client-server utxos states
        addr.outputs[0][seq_no] -= 1

    # Send transactions
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
        (send_txns_invalid or send_txns_invalid_default)()
        ensure_all_nodes_have_same_data(looper, rest_nodes)

        # Initiate view change
        # Wait until view change is finished and check that needed transactions are written.
        ensure_view_change(looper, nodes)
        ensureElectionsDone(looper, nodes)

    # Reset delays
    # Make sure that all nodes have equal state
    # (expecting that lagging_node caught up missed ones)
    ensure_all_nodes_have_same_data(looper, nodes)

    # make sure the poll is functional
    send_txns()
    ensure_all_nodes_have_same_data(looper, nodes)
