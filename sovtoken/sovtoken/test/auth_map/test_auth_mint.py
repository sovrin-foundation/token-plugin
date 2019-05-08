import json

import pytest
from sovtoken.constants import ADDRESS, AMOUNT, MINT_PUBLIC, OUTPUTS
from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request
from indy_common.authorize.auth_actions import ADD_PREFIX
from indy_common.authorize.auth_constraints import AuthConstraint
from sovtoken.sovtoken_auth_map import sovtoken_auth_map, add_mint

from plenum.common.constants import STEWARD, TXN_TYPE
from plenum.common.exceptions import RequestRejectedException


def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def steward_do_mint(helpers, outputs):
    """ Sends and check a mint txn """
    outputs_ready = helpers.request._prepare_outputs(outputs)

    payload = {
        TXN_TYPE: MINT_PUBLIC,
        OUTPUTS: outputs_ready,
    }
    identifier = helpers.wallet._steward_wallets[0].defaultId

    request = helpers.request._create_request(payload,
                                              identifier=identifier)
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
