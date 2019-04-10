import pytest
from sovtoken.constants import ADDRESS, AMOUNT
from sovtokenfees.fees_authorizer import FeesAuthorizer, FEES_FIELD_NAME

from plenum.test.testing_utils import FakeSomething
from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler
from sovtokenfees.test.helper import add_fees_request_with_address

from indy_common.authorize.auth_constraints import AuthConstraint

from indy_common.constants import NYM

from plenum.common.types import f

from plenum.common.exceptions import UnauthorizedClientRequest


@pytest.fixture()
def req_with_fees(helpers,
                  fees_set,
                  address_main,
                  fees):
    request = helpers.request.nym()
    utxos = [{ADDRESS: address_main,
              AMOUNT: fees.get(NYM),
              f.SEQ_NO.nm: 1}]
    return add_fees_request_with_address(
        helpers,
        fees_set,
        request,
        address_main,
        utxos=utxos,
    )

@pytest.fixture()
def fees_constraint(fees):
    return AuthConstraint(role='*',
                          sig_count=1,
                          need_to_be_owner=True,
                          metadata={FEES_FIELD_NAME: fees.get(NYM)})


@pytest.fixture()
def fees_req_handler():
    return FakeSomething(deducted_fees_xfer={},
                         has_fees=StaticFeesReqHandler.has_fees)


@pytest.fixture()
def fees_authorizer(fees_req_handler):
    return FeesAuthorizer(fees_req_handler)


def test_get_fees_from_constraint(fees_authorizer,
                                  fees_constraint,
                                  fees):
    assert fees_authorizer._get_fees_from_constraint(fees_constraint) == fees.get(NYM)


def test_get_fees_from_constraint_None_if_empty(fees_authorizer,
                                                fees_constraint):
    fees_constraint.metadata = {}
    assert fees_authorizer._get_fees_from_constraint(fees_constraint) is None


def test_fail_on_req_with_fees_but_fees_not_required(fees_authorizer,
                                                     req_with_fees,
                                                     fees_constraint):
    fees_constraint.metadata = {}
    with pytest.raises(UnauthorizedClientRequest, match="Fees are not required for this txn type"):
        authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                    auth_constraint=fees_constraint)


def test_fail_on_req_with_fees_but_fees_have_zero_amount(fees_authorizer,
                                                         req_with_fees,
                                                         fees_constraint):
    fees_constraint.metadata = {FEES_FIELD_NAME: 0}
    with pytest.raises(UnauthorizedClientRequest, match="Fees are not required for this txn type"):
        authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                    auth_constraint=fees_constraint)


def test_fail_on_req_without_fees_but_required(fees_authorizer,
                                               req_with_fees,
                                               fees_constraint):
    delattr(req_with_fees, 'fees')
    with pytest.raises(UnauthorizedClientRequest, match="Fees are required for this txn type"):
        authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                    auth_constraint=fees_constraint)


def test_fail_on_req_with_fees_but_cannot_pay(fees_authorizer,
                                              req_with_fees,
                                              fees_constraint):
    def raise_some_exp():
        raise KeyError("bla bla bla")
    fees_authorizer.fees_req_handler.can_pay_fees = lambda *args, **kwargs: raise_some_exp()
    with pytest.raises(UnauthorizedClientRequest, match="Cannot pay fees"):
        authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                    auth_constraint=fees_constraint)


def test_success_authorization(fees_authorizer,
                               req_with_fees,
                               fees_constraint):
    fees_authorizer.fees_req_handler.can_pay_fees = lambda *args, **kwargs: True
    authorized, msg = fees_authorizer.authorize(request=req_with_fees,
                                                auth_constraint=fees_constraint)
    assert authorized and not msg
