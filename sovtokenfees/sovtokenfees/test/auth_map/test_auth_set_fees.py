import json

import pytest
from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request
from indy_common.authorize.auth_actions import ADD_PREFIX, EDIT_PREFIX
from indy_common.authorize.auth_constraints import AuthConstraint, AuthConstraintForbidden
from sovtokenfees.constants import SET_FEES, FEES
from sovtokenfees.sovtokenfees_auth_map import sovtokenfees_auth_map, edit_fees
from sovtokenfees.test.auth_map.helper import set_fees

from plenum.common.constants import STEWARD, TXN_TYPE
from plenum.common.exceptions import RequestRejectedException
from sovtokenfees.test.constants import NYM_FEES_ALIAS


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(4)


def test_set_fees(helpers,
                  fees,
                  addresses,
                  looper,
                  sdk_wallet_trustee,
                  sdk_pool_handle):
    """
    1. Send a SET_FEES txn from 3 TRUSTEE
    2. Change the auth rule for editing SET_FEES to 1 STEWARD signature
    3. Send a transfer from 3 TRUSTEE, check that auth validation failed.
    4. Send and check that a SET_FEES request with STEWARD signature pass.
    5. Change the auth rule to a default value.
    6. Send and check a SET_FEES txn from 3 TRUSTEE.
    """
    set_fees(helpers, fees)

    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_pool_handle,
                                         sdk_wallet_trustee,
                                         auth_action=EDIT_PREFIX,
                                         auth_type=SET_FEES,
                                         field='*',
                                         old_value='*',
                                         new_value='*',
                                         constraint=AuthConstraint(role=STEWARD, sig_count=1,
                                                                   need_to_be_owner=False).as_dict)

    with pytest.raises(RequestRejectedException, match="Not enough STEWARD signatures"):
        set_fees(helpers, fees)
    set_fees(helpers, fees, trustee=False)

    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_pool_handle,
                                         sdk_wallet_trustee,
                                         auth_action=EDIT_PREFIX,
                                         auth_type=SET_FEES,
                                         field='*',
                                         old_value='*',
                                         new_value='*',
                                         constraint=sovtokenfees_auth_map[edit_fees.get_action_id()].as_dict)
    set_fees(helpers, fees)


def test_forbid_set_fees(helpers,
                         fees,
                         addresses,
                         looper,
                         sdk_wallet_trustee,
                         sdk_pool_handle):
    """
    1. Send a SET_FEES txn.
    2. Forbid SET_FEES via the auth rule for editing SET_FEES.
    3. Send a SET_FEES txn and check that action forbidden.
    4. Change the auth rule to a default value.
    6. Send and check a SET_FEES txn.
    """
    set_fees(helpers, fees)

    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_pool_handle,
                                         sdk_wallet_trustee,
                                         auth_action=EDIT_PREFIX,
                                         auth_type=SET_FEES,
                                         field='*',
                                         old_value='*',
                                         new_value='*',
                                         constraint=AuthConstraintForbidden().as_dict)

    with pytest.raises(RequestRejectedException, match=str(AuthConstraintForbidden())):
        set_fees(helpers, fees)

    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_pool_handle,
                                         sdk_wallet_trustee,
                                         auth_action=EDIT_PREFIX,
                                         auth_type=SET_FEES,
                                         field='*',
                                         old_value='*',
                                         new_value='*',
                                         constraint=sovtokenfees_auth_map[edit_fees.get_action_id()].as_dict)
    set_fees(helpers, fees)
