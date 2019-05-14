import json

import pytest
from sovtoken.constants import ADDRESS, AMOUNT, MINT_PUBLIC, OUTPUTS, TOKEN_LEDGER_ID
from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request
from indy_common.authorize.auth_actions import ADD_PREFIX
from indy_common.authorize.auth_constraints import AuthConstraint
from sovtoken.sovtoken_auth_map import sovtoken_auth_map, add_mint

from indy_node.test.helper import start_stopped_node
from sovtokenfees.test.helper import ensure_all_nodes_have_same_data

from plenum.common.constants import STEWARD, TXN_TYPE
from plenum.common.exceptions import RequestRejectedException
from plenum.test.pool_transactions.helper import disconnect_node_and_ensure_disconnected


def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def steward_do_mint(helpers, outputs):
    """ Sends and check a mint txn """
    request = helpers.request.mint(outputs)
    request.signatures = {}
    request._identifier = helpers.wallet._stewards[0]
    request = json.dumps(request.as_dict)
    request = helpers.wallet.sign_request_stewards(request)
    request = json.loads(request)
    sigs = request["signatures"]
    request = helpers.sdk.sdk_json_to_request_object(request)
    setattr(request, "signatures", sigs)
    return helpers.sdk.send_and_check_request_objects([request])


def test_auth_mint_after_node_restart(helpers,
                                      addresses,
                                      looper,
                                      sdk_wallet_trustee,
                                      sdk_pool_handle,
                                      txnPoolNodeSet,
                                      tconf,
                                      tdir,
                                      allPluginsPath,
                                      do_post_node_creation):
    """
    1. Send a MINT_PUBLIC txn from 3 TRUSTEE
    2. Change the auth rule for adding MINT_PUBLIC to 1 STEWARD signature
    3. Send a transfer from 3 TRUSTEE, check that auth validation failed.
    4. Restart 2 nodes
    5. Send and check that a MINT_PUBLIC request with STEWARD signature pass.
    6. Change the auth rule to a default value.
    7. Send and check a MINT_PUBLIC txn from 3 TRUSTEE.
    """
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    helpers.general.do_mint(outputs)

    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_wallet_trustee,
                                         sdk_pool_handle,
                                         auth_action=ADD_PREFIX,
                                         auth_type=MINT_PUBLIC,
                                         field='*',
                                         new_value='*',
                                         constraint=AuthConstraint(role=STEWARD, sig_count=1,
                                                                   need_to_be_owner=False).as_dict)

    _restart_node(txnPoolNodeSet, looper, tconf, tdir, allPluginsPath, do_post_node_creation, -1)
    _restart_node(txnPoolNodeSet, looper, tconf, tdir, allPluginsPath, do_post_node_creation, -2)
    helpers.node.reset_fees()
    ensure_all_nodes_have_same_data(looper, txnPoolNodeSet)

    with pytest.raises(RequestRejectedException, match="Not enough STEWARD signatures"):
        helpers.general.do_mint(outputs)

    steward_do_mint(helpers, outputs)
    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_wallet_trustee,
                                         sdk_pool_handle,
                                         auth_action=ADD_PREFIX,
                                         auth_type=MINT_PUBLIC,
                                         field='*',
                                         new_value='*',
                                         constraint=sovtoken_auth_map[add_mint.get_action_id()].as_dict)

    helpers.general.do_mint(outputs)


def _restart_node(txnPoolNodeSet, looper, tconf, tdir, allPluginsPath, do_post_node_creation, node_index):
    node_to_disconnect = txnPoolNodeSet[node_index]
    disconnect_node_and_ensure_disconnected(looper,
                                            txnPoolNodeSet,
                                            node_to_disconnect.name,
                                            stopNode=True)
    looper.removeProdable(node_to_disconnect)
    restarted_node = start_stopped_node(node_to_disconnect, looper,
                                        tconf, tdir, allPluginsPath,
                                        start=False)
    do_post_node_creation(restarted_node)
    looper.add(restarted_node)
    txnPoolNodeSet[node_index] = restarted_node
