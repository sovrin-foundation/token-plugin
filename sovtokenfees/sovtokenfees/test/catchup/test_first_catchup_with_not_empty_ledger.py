import pytest
from sovtoken.constants import ADDRESS, AMOUNT, TOKEN_LEDGER_ID

from plenum.test.pool_transactions.helper import disconnect_node_and_ensure_disconnected, sdk_add_new_steward_and_node, \
    sdk_add_new_nym, prepare_nym_request, sdk_add_new_node

from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_transfer, \
    send_and_check_nym_with_fees

from plenum.test.view_change.helper import ensure_view_change, start_stopped_node

from plenum.test.test_node import ensureElectionsDone, checkNodesConnected

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data, waitNodeDataEquality


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(4)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def test_first_catchup_with_not_empty_ledger(looper, helpers,
                                             nodeSetWithIntegratedTokenPlugin,
                                             sdk_pool_handle,
                                             sdk_wallet_trustee,
                                             fees_set,
                                             mint_tokens, addresses, fees,
                                             tconf,
                                             tdir, allPluginsPath, do_post_node_creation):
    node_set = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = 1
    reverted_node = node_set[-1]
    idx = node_set.index(reverted_node)

    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount)

    disconnect_node_and_ensure_disconnected(looper,
                                            node_set,
                                            reverted_node)
    reverted_node.ledger_to_req_handler[TOKEN_LEDGER_ID].utxo_cache._store.close()
    looper.removeProdable(name=reverted_node.name)

    from_a_to_b = [addresses[0], addresses[1]]
    from_b_to_c = [addresses[1], addresses[2]]
    from_c_to_d = [addresses[2], addresses[3]]
    from_d_to_a = [addresses[3], addresses[0]]

    # current_amount, seq_no, _ = add_nym_with_fees(helpers, fees_set, seq_no, looper, addresses, current_amount)
    current_amount, seq_no, _ = send_and_check_transfer(helpers, from_a_to_b, fees, looper,
                                                        current_amount, seq_no, transfer_summ=current_amount)
    current_amount, seq_no, _ = send_and_check_transfer(helpers, from_b_to_c, fees, looper,
                                                        current_amount, seq_no, transfer_summ=current_amount)
    current_amount, seq_no, _ = send_and_check_transfer(helpers, from_c_to_d, fees, looper,
                                                        current_amount, seq_no, transfer_summ=current_amount)

    # add node_to_disconnect to pool
    node_to_disconnect = start_stopped_node(reverted_node, looper, tconf,
                                            tdir, allPluginsPath, start=False)
    do_post_node_creation(node_to_disconnect)
    looper.add(node_to_disconnect)

    node_set[idx] = node_to_disconnect
    looper.run(checkNodesConnected(node_set))

    current_amount, seq_no, _ = send_and_check_transfer(helpers, from_d_to_a, fees, looper,
                                                        current_amount, seq_no, transfer_summ=current_amount)
    ensure_all_nodes_have_same_data(looper, node_set)
