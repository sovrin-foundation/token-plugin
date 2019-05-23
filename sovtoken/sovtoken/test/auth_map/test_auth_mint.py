import json
from collections import OrderedDict

import pytest
from sovtoken.constants import ADDRESS, AMOUNT, MINT_PUBLIC, OUTPUTS
from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request, sdk_get_auth_rule_request
from indy_common.authorize.auth_actions import ADD_PREFIX
from indy_common.authorize.auth_constraints import AuthConstraint
from sovtoken.sovtoken_auth_map import sovtoken_auth_map, add_mint

from indy_node.server.config_req_handler import ConfigReqHandler

from indy_common.constants import CONSTRAINT

from indy_common.authorize.auth_map import auth_map
from plenum.common.constants import STEWARD, TXN_TYPE, DATA
from plenum.common.exceptions import RequestRejectedException


def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def steward_do_mint(helpers, outputs):
    """ Sends and check a mint txn """
    request = helpers.request.mint(outputs)

    request.signatures = {}
    request._identifier = helpers.wallet._stewards[0]

    request = helpers.wallet.sign_request_stewards(json.dumps(request.as_dict),
                                                   number_signers=1)
    helpers.sdk.sdk_send_and_check([request])


@pytest.fixture
def addresses(helpers):
    return helpers.wallet.create_new_addresses(5)


def test_auth_mint(helpers,
                   addresses,
                   looper,
                   sdk_wallet_trustee,
                   sdk_pool_handle):
    """
    1. Send a MINT_PUBLIC txn from 3 TRUSTEE
    2. Change the auth rule for adding MINT_PUBLIC to 1 STEWARD signature
    3. Send a transfer from 3 TRUSTEE, check that auth validation failed.
    4. Send and check that a MINT_PUBLIC request with STEWARD signature pass.
    5. Change the auth rule to a default value.
    6. Send and check a MINT_PUBLIC txn from 3 TRUSTEE.
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

    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
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
    resp = sdk_get_auth_rule_request(looper,
                                     sdk_wallet_trustee,
                                     sdk_pool_handle)
    full_auth_map = OrderedDict(auth_map)
    full_auth_map.update(sovtoken_auth_map)

    result = resp[0][1]["result"][DATA]
    for i, (auth_key, constraint) in enumerate(full_auth_map.items()):
        rule = result[i]
        assert auth_key == ConfigReqHandler.get_auth_key(rule)
        if constraint is None:
            assert {} == rule[CONSTRAINT]
        else:
            assert constraint.as_dict == rule[CONSTRAINT]
