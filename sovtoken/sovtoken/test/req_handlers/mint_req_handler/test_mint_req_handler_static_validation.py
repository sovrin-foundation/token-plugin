import pytest
from base58 import b58encode_check
from sovtoken.constants import OUTPUTS, AMOUNT, ADDRESS

from plenum.common.exceptions import InvalidClientRequest, UnknownIdentifier
from plenum.common.util import randomString


def test_mint_handler_static_validation_valid(mint_handler, mint_request):
    mint_handler.static_validation(mint_request)


def test_mint_handler_static_validation_no_outputs_field(mint_handler, mint_request):
    del mint_request.operation[OUTPUTS]
    with pytest.raises(InvalidClientRequest, match="outputs needs to be present"):
        mint_handler.static_validation(mint_request)


def test_mint_handler_static_validation_no_outputs(mint_handler, mint_request):
    mint_request.operation[OUTPUTS].clear()
    with pytest.raises(InvalidClientRequest, match="Outputs for a mint request can't be empty."):
        mint_handler.static_validation(mint_request)


def test_mint_handler_static_validation_invalid_length_address(mint_handler, mint_request):
    operation = mint_request.operation
    addr = b58encode_check(randomString(31).encode()).decode()
    operation[OUTPUTS][0][ADDRESS] = addr
    with pytest.raises(InvalidClientRequest, match="Not a valid address as it resolves to 31 byte verkey"):
        mint_handler.static_validation(mint_request)


def test_mint_handler_static_validation_invalid_checksum_address(mint_handler, mint_request):
    operation = mint_request.operation
    operation[OUTPUTS][0][ADDRESS] = operation[OUTPUTS][0][ADDRESS][:-1] + '1'\
        if '1' != operation[OUTPUTS][0][ADDRESS][-1] else '2'
    with pytest.raises(UnknownIdentifier,
                       match="{} is not a valid base58check value".format(operation[OUTPUTS][0][ADDRESS].encode())):
        mint_handler.static_validation(mint_request)


def test_mint_handler_static_validation_invalid_amount(mint_handler, mint_request):
    mint_request.operation[OUTPUTS][0][AMOUNT] = -1
    with pytest.raises(InvalidClientRequest, match="negative or zero value"):
        mint_handler.static_validation(mint_request)


def test_mint_handler_static_validation_duplicate_addresses(mint_handler, mint_request):
    mint_request.operation[OUTPUTS].append(mint_request.operation[OUTPUTS][0])
    with pytest.raises(InvalidClientRequest, match="Each output should contain unique address"):
        mint_handler.static_validation(mint_request)
