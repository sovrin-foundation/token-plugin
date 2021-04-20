import pytest
from sovtoken.request_handlers.token_utils import TokenStaticHelper

from plenum.common.exceptions import InvalidClientMessageException

from sovtoken.exceptions import ExtraFundsError


def test_xfer_public_txn_equal():
    TokenStaticHelper.validate_given_inputs_outputs(1, 1, 1, None)
    TokenStaticHelper.validate_given_inputs_outputs(10, 10, 10, None)
    TokenStaticHelper.validate_given_inputs_outputs(100, 100, 100, None)
    TokenStaticHelper.validate_given_inputs_outputs(100000000000000, 100000000000000, 100000000000000, None)
    TokenStaticHelper.validate_given_inputs_outputs(9223372036854775807, 9223372036854775807, 9223372036854775807, None)
    TokenStaticHelper.validate_given_inputs_outputs(9223372036854775807000, 9223372036854775807000, 9223372036854775807000, None)


def test_xfer_public_txn_inputs_not_greater():
    with pytest.raises(ExtraFundsError):
        TokenStaticHelper.validate_given_inputs_outputs(2, 1, 1, None)

    with pytest.raises(InvalidClientMessageException):
        TokenStaticHelper.validate_given_inputs_outputs(1, 2, 2, None)

    with pytest.raises(InvalidClientMessageException):
        TokenStaticHelper.validate_given_inputs_outputs(100000000000000000000000, 100000000000000000000001, 100000000000000000000001, None)
