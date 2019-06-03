import pytest
from sovtoken.test.constants import VALID_IDENTIFIER

from plenum.common.exceptions import UnauthorizedClientRequest


def test_mint_handler_dynamic_validation_valid_request(mint_handler, mint_request):
    mint_handler.dynamic_validation(mint_request)


def test_mint_handler_dynamic_validation_not_enough_signatures(mint_handler, mint_request):
    mint_request.signatures = dict([(k, v) for k, v in mint_request.signatures.items()][:-1])
    with pytest.raises(UnauthorizedClientRequest, match='Not enough TRUSTEE signatures'):
        mint_handler.dynamic_validation(mint_request)


def test_mint_handler_dynamic_validation_unknown_identifier(mint_handler, mint_request):
    mint_request._identifier = VALID_IDENTIFIER
    with pytest.raises(UnauthorizedClientRequest, match="sender's DID {} is not found in the Ledger".format(VALID_IDENTIFIER)):
        mint_handler.dynamic_validation(mint_request)