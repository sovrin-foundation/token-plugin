import shutil

import pytest
from sovtoken.constants import ADDRESS, AMOUNT, XFER_PUBLIC
from indy_common.config_helper import NodeConfigHelper
from sovtoken.sovtoken_auth_map import sovtoken_auth_map
from sovtokenfees.constants import FEES_FIELD_NAME
from sovtokenfees.test.constants import NYM_FEES_ALIAS, XFER_PUBLIC_FEES_ALIAS
from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_transfer, \
    send_and_check_nym_with_fees

from indy_common.authorize.auth_actions import ADD_PREFIX, AuthActionAdd, AbstractAuthAction

from indy_common.constants import NYM

from indy_common.authorize.auth_map import auth_map
from plenum.test.test_node import checkNodesConnected, ensure_node_disconnected
from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data, waitNodeDataEquality
from indy_node.test.helper import start_stopped_node, TestNode, sdk_send_and_check_auth_rule_request


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(4)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


@pytest.fixture()
def fees_set(helpers, looper, sdk_pool_handle, sdk_wallet_trustee):
    fees = {NYM_FEES_ALIAS: 2,
            XFER_PUBLIC_FEES_ALIAS: 8}
    helpers.general.set_fees_without_waiting(fees, fill_auth_map=False)

    add_fees_auth_to_auth_rule(looper, sdk_pool_handle,
                               sdk_wallet_trustee,
                               AuthActionAdd(txn_type=XFER_PUBLIC,
                                             field="*",
                                             value="*"),
                               XFER_PUBLIC_FEES_ALIAS)
    add_fees_auth_to_auth_rule(looper, sdk_pool_handle,
                               sdk_wallet_trustee,
                               AuthActionAdd(txn_type=NYM,
                                             field="role",
                                             value=None),
                               NYM_FEES_ALIAS)
    return {'fees': fees}


def add_fees_auth_to_auth_rule(looper, sdk_pool_handle, sdk_wallet_trustee, key: AuthActionAdd, fees_alias):
    auth_map.update(sovtoken_auth_map)
    constraint = auth_map[key.get_action_id()]
    constraint.set_metadata({FEES_FIELD_NAME: fees_alias})
    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_pool_handle,
                                         sdk_wallet_trustee,
                                         auth_action=ADD_PREFIX,
                                         auth_type=key.txn_type,
                                         field=key.field,
                                         new_value=key.value,
                                         constraint=constraint.as_dict)


def test_state_recover_from_ledger(looper, tconf, tdir,
                                   sdk_pool_handle,
                                   sdk_wallet_trustee,
                                   allPluginsPath,
                                   fees_set,
                                   mint_tokens, addresses, fees,
                                   do_post_node_creation,
                                   nodeSetWithIntegratedTokenPlugin,
                                   helpers):
    node_set = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = 1

    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount)
    current_amount, seq_no, _ = send_and_check_transfer(helpers, [addresses[0], addresses[1]], fees, looper,
                                                        current_amount, seq_no,
                                                        transfer_summ=current_amount)

    current_amount, seq_no, _ = send_and_check_transfer(helpers, [addresses[1], addresses[2]], fees, looper,
                                                        current_amount, seq_no,
                                                        transfer_summ=current_amount)

    ensure_all_nodes_have_same_data(looper, node_set)

    node_to_stop = node_set[-1]
    state_db_pathes = [state._kv.db_path
                       for state in node_to_stop.states.values()]
    node_to_stop.cleanupOnStopping = False
    node_to_stop.stop()
    looper.removeProdable(node_to_stop)
    ensure_node_disconnected(looper, node_to_stop, node_set[:-1])

    for path in state_db_pathes:
        shutil.rmtree(path)
    config_helper = NodeConfigHelper(node_to_stop.name, tconf, chroot=tdir)
    restarted_node = TestNode(
        node_to_stop.name,
        config_helper=config_helper,
        config=tconf,
        pluginPaths=allPluginsPath,
        ha=node_to_stop.nodestack.ha,
        cliha=node_to_stop.clientstack.ha)
    do_post_node_creation(restarted_node)

    looper.add(restarted_node)
    node_set = node_set[:-1]

    looper.run(checkNodesConnected(node_set))
    waitNodeDataEquality(looper, restarted_node, *node_set[:-1])

    ensure_all_nodes_have_same_data(looper, node_set)

    current_amount, seq_no, _ = send_and_check_transfer(helpers, [addresses[2], addresses[0]], fees, looper,
                                                        current_amount, seq_no,
                                                        transfer_summ=current_amount)

    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount)
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount)

    ensure_all_nodes_have_same_data(looper, node_set)
