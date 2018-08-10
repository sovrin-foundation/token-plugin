import pytest
from plenum.common.constants import TRUSTEE, STEWARD, ROLE
from plenum.common.exceptions import InvalidClientMessageException

from sovtoken.exceptions import ExtraFundsError
from sovtoken.token_req_handler import TokenReqHandler


def test_mint_no_senders():
    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_mint_public_txn(None, None, 1)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_mint_public_txn(None, [], 1)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_mint_public_txn(None, [1], 1)


def test_mint_not_enough_trusties():
    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_mint_public_txn(None, [{ROLE: STEWARD}], 1)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_mint_public_txn(None, [{ROLE: TRUSTEE}], 2)

    TokenReqHandler._validate_mint_public_txn(None, [{ROLE: TRUSTEE}, {ROLE: TRUSTEE}], 2)
    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_mint_public_txn(None, [{ROLE: TRUSTEE}, {ROLE: STEWARD}], 2)


def test_xfer_public_txn_equal():
    TokenReqHandler._validate_xfer_public_txn(None, 1, 1, False)
    TokenReqHandler._validate_xfer_public_txn(None, 10, 10, False)
    TokenReqHandler._validate_xfer_public_txn(None, 100, 100, False)
    TokenReqHandler._validate_xfer_public_txn(None, 100000000000000, 100000000000000, False)
    TokenReqHandler._validate_xfer_public_txn(None, 9223372036854775807, 9223372036854775807, False)
    TokenReqHandler._validate_xfer_public_txn(None, 9223372036854775807000, 9223372036854775807000, False)


def test_xfer_public_txn_inputs_not_greater():
    with pytest.raises(ExtraFundsError):
        TokenReqHandler._validate_xfer_public_txn(None, 2, 1, False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, 1, 2, False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, 100000000000000000000000, 100000000000000000000001, False)


def test_xfer_public_txn_not_int():
    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, 1, None, False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, 1, "", False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, 1, "1", False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, 1.2, 1.2, False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, None, 1, False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, "", 1, False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, "1", 1, False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, None, None, False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, "", "", False)

    with pytest.raises(InvalidClientMessageException):
        TokenReqHandler._validate_xfer_public_txn(None, "1", "1", False)