import pytest
from sovtoken.test.constants import VALID_IDENTIFIER

from plenum.common.exceptions import UnauthorizedClientRequest


def test_set_fees_dynamic_validation(set_fees_request, set_fees_handler):
    set_fees_handler.dynamic_validation(set_fees_request)


def test_set_fees_insufficient_signatures(set_fees_request, set_fees_handler):
    set_fees_request.signatures = {
        set_fees_request.identifier: set_fees_request.signatures[set_fees_request.identifier]}
    with pytest.raises(UnauthorizedClientRequest, match='Not enough TRUSTEE signatures'):
        set_fees_handler.dynamic_validation(set_fees_request)


def test_set_fees_handler_dynamic_validation_unknown_identifier(set_fees_handler, set_fees_request):
    set_fees_request._identifier = VALID_IDENTIFIER
    with pytest.raises(UnauthorizedClientRequest,
                       match="sender's DID {} is not found in the Ledger".format(VALID_IDENTIFIER)):
        set_fees_handler.dynamic_validation(set_fees_request)
