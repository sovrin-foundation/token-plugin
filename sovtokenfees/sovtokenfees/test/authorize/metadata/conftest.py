from itertools import combinations, product

import functools
import pytest

from indy_common.authorize.auth_constraints import IDENTITY_OWNER
from indy_common.constants import TRUST_ANCHOR
from indy_common.test.auth.metadata.helper import PluginAuthorizer
from plenum.common.constants import TRUSTEE, STEWARD
from plenum.test.conftest import getValueFromModule
from sovtokenfees.fees_authorizer import FeesAuthorizer

from indy_common.test.auth.conftest import write_auth_req_validator as warv, idr_cache, \
    constraint_serializer, config_state, write_request_validation


ROLES = [TRUSTEE, STEWARD, TRUST_ANCHOR, IDENTITY_OWNER]
MAX_SIG_COUNT = 3


@pytest.fixture(scope='module')
def write_auth_req_validator(warv, helpers):
    fee_handler = helpers.node.get_fees_req_handler()
    fees_authorizer = FeesAuthorizer(fees_req_handler=fee_handler,
                                     config_state=warv.config_state,
                                     utxo_cache=fee_handler.utxo_cache)
    def _mocked_cpf(self, req, required_fees):
        return req.fees == required_fees, ''
    def _mocked_cffr(self, request):
        return request.fees
    fees_authorizer.can_pay_fees = functools.partial(_mocked_cpf, fees_authorizer)
    fees_authorizer._calculate_fees_from_req = functools.partial(_mocked_cffr, fees_authorizer)
    warv.register_authorizer(fees_authorizer)
    return warv


@pytest.fixture(scope='module', params=[None, 0, 1, 2, 3, 4, 100])
def amount(request):
    return request.param


@pytest.fixture(scope='module', params=[True, False])
def is_owner(request):
    return request.param


@pytest.fixture(
    scope='module',
    params=[role for r in range(len(ROLES) + 1) for role in combinations(ROLES, r)],
    ids=[str(role) for r in range(len(ROLES) + 1) for role in combinations(ROLES, r)]
)
def roles(request):
    '''
    Combination of all roles.

    Example:
      - roles=[A, B, C]
      ==> [(A), (B), (C), (A, B), (A, C), (B, C), (A, B, C)]
    '''
    return request.param


@pytest.fixture(scope='module')
def signatures(request, roles):
    '''
    Combinations of all signature types and signature count.

    Example:
          - roles=[A, B]
          - sig_count=1..3
          =>[(), (A: 1), (B:1), (A: 2), (B: 2), (A: 3), (B: 3),
             (A:1, B: 1), (A:2, B: 1), (A:1, B: 2), (A:2, B: 2),
             (A:1, B: 3), (A:3, B: 1), (A:3, B: 3),
             (A:2, B: 3), (A:3, B: 2)]

    '''
    max_sig_count = getValueFromModule(request, "MAX_SIG_COUNT", 3)
    all_sigs_count = list(range(1, max_sig_count))
    return [
        {role: sig_count for role, sig_count in zip(roles, sigs_count)}
        for sigs_count in product(all_sigs_count, repeat=len(roles))
    ]
