import json

import pytest
from sovtokenfees.test.helper import add_fees_request_with_address, ensure_all_nodes_have_same_data, nyms_with_fees, \
    get_amount_from_token_txn

from plenum.common.exceptions import RequestRejectedException

from plenum.test.helper import sdk_send_and_check, sdk_sign_request_from_dict

from indy_common.authorize.auth_map import auth_map, add_new_identity_owner

from indy_common.constants import NYM

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.authorize.auth_actions import ADD_PREFIX


def test_validation_nym_with_zero_fees(helpers,
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
    2. Send auth_rule txn with zero fees in metadata
    3. Resend nym with fees and check, that it will be rejected, because fees is 0, but fees are set in request
    """
    amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1
    request1, request2 = nyms_with_fees(2,
                                        helpers,
                                        {'fees': {NYM: 0}},
                                        address_main,
                                        amount,
                                        init_seq_no=init_seq_no)
    with pytest.raises(RequestRejectedException, match="Fees are not required for this txn type"):
        sdk_send_and_check([json.dumps(request1.as_dict)], looper, nodeSetWithIntegratedTokenPlugin, sdk_pool_handle)

    original_action = add_new_identity_owner
    original_constraint = auth_map.get(add_new_identity_owner.get_action_id())
    original_constraint.set_metadata({'fees': 0})
    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_wallet_trustee,
                                         sdk_pool_handle,
                                         auth_action=ADD_PREFIX, auth_type=NYM,
                                         field=original_action.field, new_value=original_action.value,
                                         old_value=None, constraint=original_constraint.as_dict)
    with pytest.raises(RequestRejectedException, match="Fees are not required for this txn type"):
        sdk_send_and_check([json.dumps(request2.as_dict)], looper, nodeSetWithIntegratedTokenPlugin, sdk_pool_handle)
    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)