import json

from base58 import b58encode_check

import pytest
from sovtoken.constants import ADDRESS, FROM_SEQNO

from plenum.common.exceptions import InvalidClientRequest, UnknownIdentifier
from plenum.common.util import randomString
from plenum.test.helper import sdk_json_to_request_object


def test_valid_get_utxo_request(get_utxo_handler, get_utxo_request):
    get_utxo_handler.static_validation(get_utxo_request)


def test_get_utxo_request_no_address(get_utxo_handler, get_utxo_request):
    operation = get_utxo_request.operation
    del operation[ADDRESS]
    with pytest.raises(InvalidClientRequest, match="address needs to be provided"):
        get_utxo_handler.static_validation(get_utxo_request)


def test_get_utxo_request_invalid_checksum_address(get_utxo_handler, get_utxo_request):
    operation = get_utxo_request.operation
    operation[ADDRESS] = operation[ADDRESS][:-1] + '1' if '1' != operation[ADDRESS][-1] else '2'
    with pytest.raises(UnknownIdentifier,
                       match="{} is not a valid base58check value".format(operation[ADDRESS].encode())):
        get_utxo_handler.static_validation(get_utxo_request)


def test_get_utxo_request_invalid_vk_length(get_utxo_handler, get_utxo_request):
    operation = get_utxo_request.operation
    addr = b58encode_check(randomString(31).encode()).decode()
    operation[ADDRESS] = addr
    with pytest.raises(InvalidClientRequest,
                       match="Not a valid address as it resolves to 31 byte verkey"):
        get_utxo_handler.static_validation(get_utxo_request)


def test_get_utxo_request_invalid_from_seqno(get_utxo_handler, get_utxo_request):
    operation = get_utxo_request.operation
    operation[FROM_SEQNO] = "next"
    with pytest.raises(InvalidClientRequest, match="'{}' validation failed".format(FROM_SEQNO)):
        get_utxo_handler.static_validation(get_utxo_request)
