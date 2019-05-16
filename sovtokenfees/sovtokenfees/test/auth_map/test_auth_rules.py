import sys
from typing import NamedTuple, Dict

import pytest
from indy_common.authorize.auth_constraints import AuthConstraint, ROLE, AuthConstraintOr, AbstractAuthConstraint, \
    IDENTITY_OWNER

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.constants import NYM

from indy_common.authorize.auth_actions import EDIT_PREFIX
from sovtokenfees.test.helper import add_fees_request_with_address

from plenum.common.constants import TRUSTEE, STEWARD

auth_constraint = AuthConstraint(role=TRUSTEE, sig_count=1, need_to_be_owner=False)

fee_1 = ("fee_1", 1)
fee_2 = ("fee_2", 2)
fee_5 = ("fee_5", 5)
fee_6 = ("fee_6", 6)
fee_100 = ("fee_100", 100)

set_fees = dict([fee_1,
                 fee_2,
                 fee_5,
                 fee_6,
                 fee_100])

FEES_FIELD_NAME = "fees"

# class InputParam:
#
#     def __init__(self, auth_constraint, fees, wallets, address_main) -> None:
#         self.auth_constraint = auth_constraint
#         self.fees = fees
#         self.wallets = wallets
#         self.auth_constraint = auth_constraint
#

RequestParams = NamedTuple("RequestParams", [("fees", Dict[str, int]),
                                             ("wallets", Dict[str, int]),
                                             ("address", str)]
                           )

InputParam = NamedTuple("InputParam", [
    ("auth_constraint", AbstractAuthConstraint),
    ("valid_requests", [RequestParams]),
    ("invalid_requests", [RequestParams])])

steward_address = ""
trustee_address = ""
owner_address = ""

input_params_map = [InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                                 AuthConstraint(TRUSTEE, 1)]),
                               valid_requests=[
                                   RequestParams(fees=dict([fee_5]),
                                                 wallets={STEWARD: 1},
                                                 address=steward_address),
                                   RequestParams(fees={},
                                                 wallets={TRUSTEE: 1},
                                                 address=trustee_address),
                                   RequestParams(fees=dict([fee_5]),
                                                 wallets={TRUSTEE: 1,
                                                          STEWARD: 1},
                                                 address=trustee_address),
                               ],
                               invalid_requests=[
                                   RequestParams(fees=dict([fee_1]),
                                                 wallets={STEWARD: 1},
                                                 address=steward_address),
                                   RequestParams(fees=dict([fee_5]),
                                                 wallets={TRUSTEE: 1},
                                                 address=trustee_address),
                                   RequestParams(fees=dict([fee_5]),
                                                 wallets={IDENTITY_OWNER: 1},
                                                 address=owner_address)
                               ])
                    ]


@pytest.fixture(params=input_params_map)
def input_param(request):
    return request.param


@pytest.fixture(params=input_params_map)
def addresses(helpers):
    addresses = {}
    for wallet in helpers.wallet._trustee_wallets + \
                  helpers.wallet._steward_wallets + \
                  helpers.wallet._client_wallets:
        address = helpers.wallet.create_address(wallet)
        addresses[wallet.identifiers[0]] = address
    return addresses


def _send_request(helpers, fees, wallets_count):
    wallets = helpers.wallet._trustee_wallets[:wallets_count[TRUSTEE]] + \
              helpers.wallet._steward_wallets[:wallets_count[STEWARD]] + \
              helpers.wallet._trustee_wallets[:wallets_count[IDENTITY_OWNER]]
    # create request
    client_request = helpers.request.nym()
    # add fees
    address = addresses[wallets[0].identifiers[0]]
    client_request = add_fees_request_with_address(helpers,
                                                   fees,
                                                   client_request,
                                                   address)
    # sign request
    helpers.wallet.sign_request(client_request, wallets)

    return helpers.sdk.send_and_check_request_objects([client_request])


def test_authorization(looper, sdk_wallet_trustee,
                       sdk_pool_handle, helpers, request, input_param, addresses):
    input_param = request.param
    sdk_send_and_check_auth_rule_request(looper, sdk_wallet_trustee,
                                         sdk_pool_handle, auth_action=EDIT_PREFIX,
                                         auth_type=NYM, field=ROLE, new_value=STEWARD, old_value=None,
                                         constraint=input_param.auth_constraint.as_dict)
    for req in input_param.valid_requests:
        _send_request(helpers, req.fees, req.wallets)

    for req in input_param.invalid_requests:
        _send_request(helpers, req.fees, req.wallets)
