import json

import functools
import pytest
from sovtoken.constants import AMOUNT
from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no
from sovtokenfees.constants import FEES_FIELD_NAME
from sovtokenfees.fees_authorizer import FeesAuthorizer
from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler
from sovtokenfees.test.helper import add_fees_request_with_address
from indy_common.authorize.auth_constraints import AuthConstraint
from indy_common.constants import NYM
from plenum.common.exceptions import UnauthorizedClientRequest
from plenum.test.testing_utils import FakeSomething

from state.pruning_state import PruningState
from storage.kv_in_memory import KeyValueStorageInMemory


def _set_fees(authorizer, fees=None):
    fees = fees or {"1": 4}
    authorizer.config_state.set(StaticFeesReqHandler.build_path_for_set_fees().encode(),
                                json.dumps(fees).encode())


@pytest.fixture()
def req_with_fees(helpers,
                  fees_set,
                  address_main,
                  fees):
    request = helpers.request.nym()
    utxos = [{"source": utxo_from_addr_and_seq_no(address_main, 1),
              AMOUNT: fees.get(NYM)}]
    return add_fees_request_with_address(
        helpers,
        fees_set,
        request,
        address_main,
        utxos=utxos,
    )

@pytest.fixture()
def fees_constraint():
    return AuthConstraint(role='*',
                          sig_count=1,
                          need_to_be_owner=True,
                          metadata={FEES_FIELD_NAME: NYM})


@pytest.fixture()
def fees_req_handler(fees):
    handler = FakeSomething(deducted_fees_xfer={},
                            has_fees=StaticFeesReqHandler.has_fees,
                            calculate_fees_from_req=lambda *args, **kwargs: fees.get(NYM))
    return handler



@pytest.fixture()
def fees_authorizer(fees_req_handler):
    return FeesAuthorizer(fees_req_handler,
                          config_state=PruningState(KeyValueStorageInMemory()))


def test_get_fees_from_constraint(fees_authorizer,
                                  fees_constraint,
                                  fees):
    assert fees_authorizer._get_fees_alias_from_constraint(fees_constraint) == NYM


def test_get_fees_from_constraint_None_if_empty(fees_authorizer,
                                                fees_constraint):
    fees_constraint.metadata = {}
    assert fees_authorizer._get_fees_alias_from_constraint(fees_constraint) is None


def test_fail_on_req_with_fees_but_fees_not_required(fees_authorizer,
                                                     req_with_fees,
                                                     fees_constraint):
    fees_constraint.metadata = {}
    authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                auth_constraint=fees_constraint)
    assert not authorized
    assert "Fees are not required for this txn type" in msg


def test_fail_on_req_with_fees_but_fees_have_zero_amount(fees_authorizer,
                                                         req_with_fees,
                                                         fees_constraint):
    fees_constraint.metadata = {FEES_FIELD_NAME: NYM}
    _set_fees(fees_authorizer, {NYM: 0})
    authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                auth_constraint=fees_constraint)
    assert not authorized
    assert "Fees are not required for this txn type" in msg


def test_fail_on_req_without_fees_but_required(fees_authorizer,
                                               req_with_fees,
                                               fees_constraint):
    delattr(req_with_fees, 'fees')
    _set_fees(fees_authorizer)
    authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                auth_constraint=fees_constraint)
    assert not authorized
    assert  "Fees are required for this txn type" in msg


def test_fail_on_req_with_fees_but_cannot_pay(fees_authorizer,
                                              req_with_fees,
                                              fees_constraint):
    def raise_some_exp():
        raise UnauthorizedClientRequest("identifier",
                                        "reqId",
                                        "bla bla bla")

    _set_fees(fees_authorizer)
    fees_authorizer.fees_req_handler.can_pay_fees = lambda *args, **kwargs: raise_some_exp()
    authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                auth_constraint=fees_constraint)
    assert not authorized
    assert "bla bla bla" in msg


def test_success_authorization(fees_authorizer,
                               req_with_fees,
                               fees_constraint):
    _set_fees(fees_authorizer)
    fees_authorizer.fees_req_handler.can_pay_fees = lambda *args, **kwargs: True
    authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                auth_constraint=fees_constraint)
    assert authorized and not msg
