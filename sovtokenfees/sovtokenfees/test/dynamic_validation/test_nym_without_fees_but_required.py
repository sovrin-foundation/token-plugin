import pytest

from plenum.common.exceptions import RequestRejectedException
from indy_common.authorize.auth_map import add_new_identity_owner, auth_map
from indy_common.constants import NYM
from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request
from indy_common.authorize.auth_actions import ADD_PREFIX
from sovtokenfees.constants import FEES
from sovtokenfees.test.constants import NYM_FEES_ALIAS

from sovtokenfees.test.helper import send_and_check_nym_with_fees, get_amount_from_token_txn


def test_nym_without_fees_but_required(fees,
                                       helpers,
                                       nodeSetWithIntegratedTokenPlugin,
                                       sdk_wallet_steward,
                                       sdk_pool_handle,
                                       sdk_wallet_trustee,
                                       mint_tokens,
                                       address_main,
                                       looper):
    """
    Steps:
    1. Send auth_rule txn with fees in metadata
    2. Send nym without fees and check, that it will be rejected
    """
    helpers.general.do_set_fees(fees, fill_auth_map=False)
    original_action = add_new_identity_owner
    original_constraint = auth_map.get(add_new_identity_owner.get_action_id())
    original_constraint.set_metadata({'fees': NYM_FEES_ALIAS})
    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_pool_handle,
                                         sdk_wallet_trustee,
                                         auth_action=ADD_PREFIX, auth_type=NYM,
                                         field=original_action.field, new_value=original_action.value,
                                         old_value=None, constraint=original_constraint.as_dict)

    with pytest.raises(RequestRejectedException, match="Fees are required for this txn type"):
        helpers.general.do_nym()
