import pytest
from plenum.common.constants import STEWARD_STRING
from sovtoken.constants import ADDRESS, AMOUNT

from plenum.common.types import f
from sovtokenfees.test.helper import add_fees_request_with_address, send_and_check_nym_with_fees, \
    get_amount_from_token_txn, send_and_check_transfer, ensure_all_nodes_have_same_data

from plenum.test.pool_transactions.helper import sdk_add_new_node, disconnect_node_and_ensure_disconnected

from plenum.test.test_node import checkNodesConnected

from plenum.test.node_catchup.helper import waitNodeDataEquality


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(4)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def add_new_node(helpers, looper, node_set, sdk_wallet_steward, current_amount, seq_no, fees_set,
                 sdk_pool_handle, tdir, tconf, allPluginsPath, address, do_post_node_creation):
    new_did, verkey = helpers.wallet.create_did(sdk_wallet=sdk_wallet_steward)
    req = helpers.request.nym(sdk_wallet=sdk_wallet_steward,
                              alias="new_steward",
                              role=STEWARD_STRING,
                              dest=new_did,
                              verkey=verkey)
    utxos = [{ADDRESS: address,
              AMOUNT: current_amount,
              f.SEQ_NO.nm: seq_no}]
    req = add_fees_request_with_address(helpers,
                                          fees_set,
                                          req,
                                          address,
                                          utxos=utxos)
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount, nym_with_fees=req)
    new_steward_wallet_handle = sdk_wallet_steward[0], new_did
    new_node = sdk_add_new_node(
        looper,
        sdk_pool_handle,
        new_steward_wallet_handle,
        'Epsilon',
        tdir,
        tconf,
        allPluginsPath=allPluginsPath,
        do_post_node_creation=do_post_node_creation)
    node_set.append(new_node)
    looper.run(checkNodesConnected(node_set))
    waitNodeDataEquality(looper, new_node, *node_set[:-1])



@pytest.mark.skip(reason="ST-537 issue with adding new node")
def test_first_catchup_for_a_new_node(looper, helpers,
                                      nodeSetWithIntegratedTokenPlugin,
                                      sdk_pool_handle,
                                      sdk_wallet_steward,
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

    add_new_node(helpers, looper, node_set, sdk_wallet_steward, current_amount, seq_no, fees_set,
                 sdk_pool_handle, tdir, tconf, allPluginsPath, addresses[3], do_post_node_creation)

    current_amount, seq_no, _ = send_and_check_transfer(helpers, from_d_to_a, fees, looper,
                                                        current_amount, seq_no, transfer_summ=current_amount)
    ensure_all_nodes_have_same_data(looper, node_set)
