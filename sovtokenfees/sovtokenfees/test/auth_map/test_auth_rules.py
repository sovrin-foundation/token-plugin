import sys
from typing import NamedTuple, Dict

import pytest
from indy_common.authorize.auth_constraints import AuthConstraint, ROLE, AuthConstraintOr, AbstractAuthConstraint, \
    IDENTITY_OWNER

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.constants import NYM

from indy_common.authorize.auth_actions import EDIT_PREFIX
from sovtoken.constants import AMOUNT, ADDRESS
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import add_fees_request_with_address

from plenum.common.constants import TRUSTEE, STEWARD, STEWARD_STRING, TRUSTEE_STRING
from plenum.test.helper import sdk_multisign_request_object, sdk_multi_sign_request_objects
from plenum.test.pool_transactions.helper import sdk_add_new_nym

auth_constraint = AuthConstraint(role=TRUSTEE, sig_count=1, need_to_be_owner=False)

fee_1 = ("fee_1", 1)
fee_2 = ("fee_2", 2)
fee_5 = (NYM, 5)
fee_6 = ("fee_6", 6)
fee_100 = ("fee_100", 100)

set_fees = dict([
     fee_1,
    #              fee_2,
                 fee_5,
                 # fee_6,
                 # fee_100
                 ])

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
                                   # RequestParams(fees={},
                                   #               wallets={TRUSTEE: 1},
                                   #               address=trustee_address),
                                   # RequestParams(fees=dict([fee_5]),
                                   #               wallets={TRUSTEE: 1,
                                   #                        STEWARD: 1},
                                   #               address=trustee_address),
                               ],
                               invalid_requests=[
                                   # RequestParams(fees=dict([fee_1]),
                                   #               wallets={STEWARD: 1},
                                   #               address=steward_address),
                                   # RequestParams(fees=dict([fee_5]),
                                   #               wallets={TRUSTEE: 1},
                                   #               address=trustee_address),
                                   # RequestParams(fees=dict([fee_5]),
                                   #               wallets={IDENTITY_OWNER: 1},
                                   #               address=owner_address)
                               ])
                    ]


@pytest.fixture(params=input_params_map)
def input_param(request):
    return request.param


@pytest.fixture()
def mint_tokens(helpers, address):
    outputs = [{ADDRESS: address, AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


@pytest.fixture(scope='module')
def sdk_wallet_stewards(looper,
                            sdk_wallet_trustee,
                            sdk_pool_handle):
    sdk_wallet_stewards = []
    for i in range(3):
        wallet = sdk_add_new_nym(looper,
                                 sdk_pool_handle,
                                 sdk_wallet_trustee,
                                 alias='steward{}'.format(i),
                                 role=STEWARD_STRING)
        sdk_wallet_stewards.append(wallet)
    return sdk_wallet_stewards


@pytest.fixture(scope='module')
def sdk_wallet_clients(looper,
                            sdk_wallet_trustee,
                            sdk_pool_handle):
    sdk_wallet_clients = []
    for i in range(3):
        wallet = sdk_add_new_nym(looper,
                                 sdk_pool_handle,
                                 sdk_wallet_trustee,
                                 alias='client{}'.format(i))
        sdk_wallet_clients.append(wallet)
    return sdk_wallet_clients


@pytest.fixture(scope='module')
def sdk_wallet_trustees(looper,
                            sdk_wallet_trustee,
                            sdk_pool_handle):
    sdk_wallet_trustees = []
    for i in range(3):
        wallet = sdk_add_new_nym(looper,
                                 sdk_pool_handle,
                                 sdk_wallet_trustee,
                                 alias='trustee{}'.format(i),
                                 role=TRUSTEE_STRING)
        sdk_wallet_trustees.append(wallet)
    return sdk_wallet_trustees

@pytest.fixture(params=input_params_map)
def address(helpers):
    # addresses = {}
    # address = [helpers.wallet.create_address()
    # for wallet in [sdk_wallet_trustees + \
    #                sdk_wallet_stewards + \
    #                sdk_wallet_clients]:
    #     address = helpers.wallet.create_address(wallet)
    #     addresses[wallet.identifiers[0]] = address
    return helpers.wallet.create_address()


def _send_request(looper, helpers, fees, wallets_count, address,
                  sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients):
    wallets = sdk_wallet_trustees[:wallets_count.get(TRUSTEE, 0)] + \
              sdk_wallet_stewards[:wallets_count.get(STEWARD, 0)] + \
              sdk_wallet_clients[:wallets_count.get(IDENTITY_OWNER, 0)]
    # create request
    client_request = helpers.request.nym()
    # add fees
    # address = addresses[wallets[0].identifiers[0]]
    client_request = add_fees_request_with_address(helpers,
                                                   {FEES: fees},
                                                   client_request,
                                                   address)
    # sign request
    sdk_multi_sign_request_objects(looper, wallets, [client_request])

    return helpers.sdk.send_and_check_request_objects([client_request])


def test_authorization(looper, mint_tokens, sdk_wallet_trustee,
                       sdk_pool_handle, helpers, input_param, address,
                       sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients):
    helpers.inner.general.do_set_fees(set_fees)
    sdk_send_and_check_auth_rule_request(looper, sdk_wallet_trustee,
                                         sdk_pool_handle, auth_action=EDIT_PREFIX,
                                         auth_type=NYM, field=ROLE, new_value=STEWARD, old_value=None,
                                         constraint=input_param.auth_constraint.as_dict)
    for req in input_param.valid_requests:
        _send_request(looper, helpers, req.fees, req.wallets, address,
                      sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients)

    for req in input_param.invalid_requests:
        _send_request(looper, helpers, req.fees, req.wallets, address,
                      sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients)
