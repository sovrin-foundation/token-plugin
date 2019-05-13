import json

import pytest
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import add_fees_request_with_address, ensure_all_nodes_have_same_data, \
    get_amount_from_token_txn, send_and_check_nym_with_fees

from plenum.common.exceptions import RequestRejectedException

from plenum.test.helper import sdk_send_and_check, sdk_sign_request_from_dict

from indy_common.authorize.auth_map import auth_map, add_new_identity_owner

from indy_common.constants import NYM

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.authorize.auth_actions import ADD_PREFIX


def test_valid_nym_with_fees(fees,
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
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = 1

    with pytest.raises(RequestRejectedException, match="Fees are not required for this txn type"):
        current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, {FEES: fees}, seq_no, looper, [address_main],
                                                                 current_amount)
    helpers.general.do_set_fees(fees, fill_auth_map=False)
    original_action = add_new_identity_owner
    original_constraint = auth_map.get(add_new_identity_owner.get_action_id())
    original_constraint.set_metadata({'fees': NYM})
    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_wallet_trustee,
                                         sdk_pool_handle,
                                         auth_action=ADD_PREFIX, auth_type=NYM,
                                         field=original_action.field, new_value=original_action.value,
                                         old_value=None, constraint=original_constraint.as_dict)
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, {FEES: fees}, seq_no, looper, [address_main],
                                                             current_amount)
    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)