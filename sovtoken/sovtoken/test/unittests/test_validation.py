import pytest
from plenum.common.exceptions import InvalidClientMessageException

from sovtoken.exceptions import ExtraFundsError


def test_xfer_public_txn_equal():
    TokenReqHandler._validate_xfer_public_txn(None, 1, 1)
    TokenReqHandler._validate_xfer_public_txn(None, 10, 10)
    TokenReqHandler._validate_xfer_public_txn(None, 100, 100)
    TokenReqHandler._validate_xfer_public_txn(None, 100000000000000, 100000000000000)
    TokenReqHandler._validate_xfer_public_txn(None, 9223372036854775807, 9223372036854775807)
    TokenReqHandler._validate_xfer_public_txn(None, 9223372036854775807000, 9223372036854775807000)


def test_xfer_public_txn_inputs_not_greater():
    with pytest.raises(ExtraFundsError):
        TokenReqHandler._validate_xfer_public_txn(None, 2, 1)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, 1, 2)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, 100000000000000000000000, 100000000000000000000001)
