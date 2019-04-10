import json

import pytest
from sovtokenfees.test.helper import add_fees_request_with_address, ensure_all_nodes_have_same_data, \
    get_amount_from_token_txn

from plenum.common.exceptions import RequestRejectedException

from plenum.test.helper import sdk_send_and_check, sdk_sign_request_from_dict

from indy_common.authorize.auth_map import auth_map, add_new_identity_owner

from indy_common.constants import NYM

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.authorize.auth_actions import ADD_PREFIX


def test_validation_nym_with_fees_cannot_pay(fees,
                                             helpers,
                                             nodeSetWithIntegratedTokenPlugin,
                                             sdk_wallet_steward,
                                             address_main,
                                             sdk_pool_handle,
                                             sdk_wallet_trustee,
                                             mint_tokens,
                                             looper):
    """
    Steps:
    1. Checks that nym with fees will be rejected, because fees are not set
    2. Send auth_rule txn with fees in metadata
    3. Resend nym with fees and check, that it will be stored
    """
    (dest, new_verkey) = helpers.wallet.create_did(
        seed=None,
        sdk_wallet=sdk_wallet_steward
    )
    amount = get_amount_from_token_txn(mint_tokens)
    req = helpers.request.nym(dest=dest, verkey=new_verkey)
    req = add_fees_request_with_address(
        helpers,
        {'fees': fees},
        req,
        address_main
    )

    with pytest.raises(RequestRejectedException, match="Fees are not required for this txn type"):
        sdk_send_and_check([json.dumps(req.as_dict)], looper, nodeSetWithIntegratedTokenPlugin, sdk_pool_handle)

    original_action = add_new_identity_owner
    original_constraint = auth_map.get(add_new_identity_owner.get_action_id())
    original_constraint.set_metadata({'fees': fees[NYM]})
    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_wallet_trustee,
                                         sdk_pool_handle,
                                         auth_action=ADD_PREFIX, auth_type=NYM,
                                         field=original_action.field, new_value=original_action.value,
                                         old_value=None, constraint=original_constraint.as_dict)
    req = helpers.request.nym(dest=dest, verkey=new_verkey)
    req = add_fees_request_with_address(
        helpers,
        {'fees': {NYM: fees[NYM] + 1}},
        req,
        address_main
    )
    with pytest.raises(RequestRejectedException, match="Cannot pay fees"):
        sdk_send_and_check([json.dumps(req.as_dict)], looper, nodeSetWithIntegratedTokenPlugin, sdk_pool_handle)
    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)