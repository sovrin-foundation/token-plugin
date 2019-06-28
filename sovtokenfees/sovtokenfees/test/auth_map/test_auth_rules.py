import json
import sys
from typing import NamedTuple, Dict, List

import pytest
from indy.did import replace_keys_start
from indy.ledger import build_attrib_request
from indy_common.authorize.auth_constraints import AuthConstraint, ROLE, AuthConstraintOr, AbstractAuthConstraint, \
    IDENTITY_OWNER, AuthConstraintAnd, AuthConstraintForbidden

from indy_common.constants import NYM, ENDORSER, NODE, POOL_UPGRADE, POOL_RESTART, VALIDATOR_INFO, GET_SCHEMA, \
    ATTRIB, ENDORSER_STRING

from indy_common.authorize.auth_actions import EDIT_PREFIX, ADD_PREFIX
from libnacl.secret import SecretBox
from sovtoken.constants import AMOUNT, ADDRESS
from sovtokenfees.constants import FEES, FEES_FIELD_NAME
from sovtokenfees.test.helper import add_fees_request_with_address

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request
from plenum.common.constants import TRUSTEE, STEWARD, STEWARD_STRING, TRUSTEE_STRING, VERKEY, DATA
from plenum.common.exceptions import RequestRejectedException
from plenum.test.helper import sdk_multi_sign_request_objects, sdk_json_to_request_object
from plenum.test.pool_transactions.helper import sdk_add_new_nym

auth_constraint = AuthConstraint(role=TRUSTEE, sig_count=1, need_to_be_owner=False)

fee_0 = ("fee_0", 0)
fee_1 = ("fee_1", 1)
fee_2 = ("fee_2", 2)
fee_3 = ("fee_3", 3)
fee_5 = ("fee_5", 5)
fee_6 = ("fee_6", 6)
fee_100 = ("fee_100", 100)

set_fees = dict([
    fee_0,
    fee_1,
    fee_2,
    fee_3,
    fee_5,
    fee_6,
    fee_100
])

RequestParams = NamedTuple("RequestParams", [("fees", int),
                                             ("owner", str),
                                             ("wallets", Dict[str, int])]
                           )
RequestParams.__new__.__defaults__ = (None, "-1", {})

InputParam = NamedTuple("InputParam", [
    ("auth_constraint", AbstractAuthConstraint),
    ("valid_requests", List[RequestParams]),
    ("invalid_requests", List[RequestParams])])

steward_address = ""
trustee_address = ""
owner_address = ""

input_params_map = [
    # 0
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                 AuthConstraint(TRUSTEE, 1)]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 1,
                                          STEWARD: 1}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={IDENTITY_OWNER: 1})
               ]),
    # 1
    InputParam(auth_constraint=AuthConstraintAnd([AuthConstraint(STEWARD, 2,
                                                                 metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                  AuthConstraint(TRUSTEE, 1,
                                                                 metadata={FEES_FIELD_NAME: fee_5[0]})]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 2,
                                          TRUSTEE: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 3,
                                          TRUSTEE: 2}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 3}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1,
                                          TRUSTEE: 1})
               ]),
    # 2
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_2[0]}),
                                                 AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]})]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_2[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_2[1],
                                 wallets={STEWARD: 1,
                                          TRUSTEE: 1}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_6[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 1})
               ]),
    # 3
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 3,
                                                                metadata={FEES_FIELD_NAME: fee_1[0]}),
                                                 AuthConstraint(TRUSTEE, 1,
                                                                metadata={FEES_FIELD_NAME: fee_2[0]}),
                                                 AuthConstraint(IDENTITY_OWNER, 1,
                                                                metadata={FEES_FIELD_NAME: fee_100[0]}),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 3}),
                   RequestParams(fees=fee_2[1],
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_100[1],
                                 wallets={IDENTITY_OWNER: 1}),
                   RequestParams(fees=fee_100[1],
                                 wallets={STEWARD: 3,
                                          TRUSTEE: 1,
                                          IDENTITY_OWNER: 1}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 2}),
                   RequestParams(fees=fee_100[1],
                                 wallets={ENDORSER: 1}),
                   RequestParams(fees=fee_100[1],
                                 wallets={TRUSTEE: 1})
               ]),
    # 4
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 3,
                                                                metadata={FEES_FIELD_NAME: fee_1[0]}),
                                                 AuthConstraintAnd([
                                                     AuthConstraint(TRUSTEE, 1,
                                                                    metadata={FEES_FIELD_NAME: fee_0[0]}),
                                                     AuthConstraint(STEWARD, 1)])
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 3,
                                          TRUSTEE: 1}),
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 3}),
                   RequestParams(wallets={STEWARD: 1,
                                          TRUSTEE: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_1[1],
                                 wallets={ENDORSER: 1}),
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1})
               ]),
    # 5
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                need_to_be_owner=False,
                                                                metadata={FEES_FIELD_NAME: fee_3[0]}),
                                                 AuthConstraint(STEWARD, 1,
                                                                need_to_be_owner=True,
                                                                metadata={FEES_FIELD_NAME: fee_1[0]})
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_3[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_1[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_3[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 2})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 owner=STEWARD,
                                 wallets={STEWARD: 2}),
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1})
               ]),
    # 6
    InputParam(auth_constraint=AuthConstraintAnd([AuthConstraint(STEWARD, 1,
                                                                 need_to_be_owner=False,
                                                                 metadata={FEES_FIELD_NAME: fee_3[0]}),
                                                  AuthConstraint(STEWARD, 1,
                                                                 need_to_be_owner=True,
                                                                 metadata={FEES_FIELD_NAME: fee_3[0]})
                                                  ]),
               valid_requests=[
                   RequestParams(fees=fee_3[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 2}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_3[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_1[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 owner=STEWARD,
                                 wallets={STEWARD: 2})
               ]),
    # 7
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint("*", 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                 AuthConstraint(TRUSTEE, 1),
                                                 AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_0[0]}),
                                                 AuthConstraint(ENDORSER, 1),
                                                 ]),
               valid_requests=[
                   RequestParams(wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={ENDORSER: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={IDENTITY_OWNER: 1}),
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 1,
                                          TRUSTEE: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 1}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_1[1],
                                 wallets={IDENTITY_OWNER: 1}),
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 1})
               ]),
    # 8
    InputParam(auth_constraint=AuthConstraint(TRUSTEE, 3,
                                              metadata={FEES_FIELD_NAME: fee_0[0]}),
               valid_requests=[
                   RequestParams(wallets={TRUSTEE: 3}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 4})
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 3})
               ]),
    # 9
    InputParam(auth_constraint=AuthConstraint(TRUSTEE, 1),
               valid_requests=[
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 2})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 1})
               ]),
    # 10
    InputParam(auth_constraint=AuthConstraint("*", 1,
                                              need_to_be_owner=True,
                                              metadata={FEES_FIELD_NAME: fee_1[0]}),
               valid_requests=[
                   RequestParams(fees=fee_1[1],
                                 owner=IDENTITY_OWNER,
                                 wallets={IDENTITY_OWNER: 1}),
                   RequestParams(fees=fee_1[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_1[1],
                                 owner=TRUSTEE,
                                 wallets={TRUSTEE: 1,
                                          STEWARD: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1})
               ]),
    # 11
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(TRUSTEE, 3),
                                                 AuthConstraint(STEWARD, 1,
                                                                need_to_be_owner=True),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=0,
                                 owner=TRUSTEE,
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=0,
                                 owner=STEWARD,
                                 wallets={STEWARD: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 2})
               ]),
    # 12
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                 AuthConstraint(STEWARD, 2),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 2}),
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 2}),
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1})
               ]),
    # 13
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                 AuthConstraint(STEWARD, 1),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 2})
               ]),
    # 14
    InputParam(auth_constraint=AuthConstraintForbidden(),
               valid_requests=[
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 2}),
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1})
               ]),
    # 15
    InputParam(auth_constraint=AuthConstraintAnd([AuthConstraintForbidden(),
                                                  AuthConstraint(STEWARD, 1),
                                                  ]),
               valid_requests=[
               ],
               invalid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 2})
               ]),
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
def sdk_wallet_endorsers(looper,
                         sdk_wallet_trustee,
                         sdk_pool_handle):
    sdk_wallet_stewards = []
    for i in range(3):
        wallet = sdk_add_new_nym(looper,
                                 sdk_pool_handle,
                                 sdk_wallet_trustee,
                                 alias='endorsers{}'.format(i),
                                 role=ENDORSER_STRING)
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


@pytest.fixture()
def address(helpers):
    return helpers.wallet.create_address()


def add_fees_request_with_address(helpers, fee_amount, request, address):
    if fee_amount is None:
        return request
    utxos_found = helpers.general.get_utxo_addresses([address])[0]
    request_with_fees = helpers.request.add_fees(
        request,
        utxos_found,
        fee_amount,
        change_address=address
    )[0]
    request_with_fees = json.loads(request_with_fees)
    setattr(request, FEES, request_with_fees[FEES])
    return request


def _send_request(looper, helpers, fees, wallets_count, address, owner, sdk_wallet_trustee,
                  sdk_wallet_trustees, sdk_wallet_stewards,
                  sdk_wallet_clients, sdk_wallet_endorsers):
    print(wallets_count)
    wallets = sdk_wallet_trustees[:wallets_count.get(TRUSTEE, 0)] + \
              sdk_wallet_stewards[:wallets_count.get(STEWARD, 0)] + \
              sdk_wallet_clients[:wallets_count.get(IDENTITY_OWNER, 0)] + \
              sdk_wallet_endorsers[:wallets_count.get(ENDORSER, 0)]
    # prepare owner parameter
    if owner == TRUSTEE:
        sender_wallet = sdk_wallet_trustees[0]
    elif owner == STEWARD:
        sender_wallet = sdk_wallet_stewards[0]
    elif owner == IDENTITY_OWNER:
        sender_wallet = sdk_wallet_clients[0]
    elif owner == ENDORSER:
        sender_wallet = sdk_wallet_endorsers[0]
    else:
        sender_wallet = wallets[0]
    target_dest = sdk_wallet_trustee[1] if owner == "-1" else sender_wallet[1]

    # prepare data
    data = SecretBox().encrypt(json.dumps({'name': 'Jaime'}).encode()).hex()

    # create request
    request = add_attribute(looper, sender_wallet, None, target_dest, enc=data)
    request = sdk_json_to_request_object(json.loads(request))

    request.signature = None
    request.signatures = None
    # add fees
    request = add_fees_request_with_address(helpers,
                                            fees,
                                            request,
                                            address)
    # sign request
    request = sdk_multi_sign_request_objects(looper, wallets, [request])

    return helpers.sdk.sdk_send_and_check(request)


def add_attribute(looper, sdk_wallet_handle, attrib,
                  dest=None, xhash=None, enc=None):
    _, s_did = sdk_wallet_handle
    t_did = dest or s_did
    attrib_req = looper.loop.run_until_complete(
        build_attrib_request(s_did, t_did, xhash, attrib, enc))
    return attrib_req


def test_authorization(looper, mint_tokens, sdk_wallet_trustee,
                       sdk_pool_handle, helpers, input_param, address,
                       sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients,
                       sdk_wallet_endorsers):
    helpers.general.do_set_fees(set_fees, fill_auth_map=False)
    sdk_send_and_check_auth_rule_request(looper, sdk_pool_handle, sdk_wallet_trustee,
                                         auth_action=ADD_PREFIX,
                                         auth_type=ATTRIB, field="*", new_value="*",
                                         constraint=input_param.auth_constraint.as_dict)
    for req in input_param.valid_requests:
        _send_request(looper, helpers, req.fees, req.wallets, address,
                      req.owner, sdk_wallet_trustee,
                      sdk_wallet_trustees, sdk_wallet_stewards,
                      sdk_wallet_clients, sdk_wallet_endorsers)

    for req in input_param.invalid_requests:
        with pytest.raises(RequestRejectedException, match="UnauthorizedClientRequest"):
            _send_request(looper, helpers, req.fees, req.wallets, address,
                          req.owner, sdk_wallet_trustee,
                          sdk_wallet_trustees, sdk_wallet_stewards,
                          sdk_wallet_clients, sdk_wallet_endorsers)
