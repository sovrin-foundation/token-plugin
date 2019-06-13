import json

import pytest
from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request
from indy_common.authorize.auth_actions import ADD_PREFIX, EDIT_PREFIX
from indy_common.authorize.auth_constraints import AuthConstraint
from sovtokenfees.constants import SET_FEES, FEES
from sovtokenfees.sovtokenfees_auth_map import sovtokenfees_auth_map, edit_fees

from indy_common.constants import NODE, NYM
from plenum.common.constants import STEWARD, TXN_TYPE
from plenum.common.exceptions import RequestRejectedException
from sovtokenfees.test.constants import NYM_FEES_ALIAS


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(4)


def steward_do_set_fees(helpers, fees):
    """ Sends and check a set_fees txn """
    payload = {
        TXN_TYPE: SET_FEES,
        FEES: fees,
    }

    request = helpers.request._create_request(payload,
                                              identifier=helpers.wallet._stewards[0])
    request = helpers.wallet.sign_request_stewards(json.dumps(request.as_dict), number_signers=1)
    helpers.sdk.sdk_send_and_check([request])


def set_fees(helpers, fees, trustee=True):
    new_fees = dict(fees)
    new_fees[NYM_FEES_ALIAS] += 1
    if trustee:
        helpers.general.do_set_fees(new_fees)
    else:
        steward_do_set_fees(helpers, new_fees)
    get_fees = helpers.general.do_get_fees()
    assert new_fees == get_fees.get("fees")


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
