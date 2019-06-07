import pytest
from base58 import b58encode_check
from sovtoken.constants import OUTPUTS, ADDRESS, AMOUNT, INPUTS, SEQNO

from plenum.common.exceptions import InvalidClientRequest, UnknownIdentifier
from plenum.common.util import randomString


def test_xfer_handler_static_validation_valid(xfer_handler, xfer_request):
    xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_no_outputs_field(xfer_handler, xfer_request):
    del xfer_request.operation[OUTPUTS]
    with pytest.raises(InvalidClientRequest, match="outputs needs to be present"):
        xfer_handler.static_validation(xfer_request)


@pytest.mark.skip(reason="This test covers a missing case -- we should not be able to send XFER request without "
                         "outputs, it is just senseless")
def test_xfer_handler_static_validation_outputs_empty(xfer_handler, xfer_request):
    xfer_request.operation[OUTPUTS].clear()
    with pytest.raises(InvalidClientRequest, match="Outputs for a xfer request can't be empty."):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_outputs_invalid_length_address(xfer_handler, xfer_request):
    operation = xfer_request.operation
    addr = b58encode_check(randomString(31).encode()).decode()
    operation[OUTPUTS][0][ADDRESS] = addr
    with pytest.raises(InvalidClientRequest, match="Not a valid address as it resolves to 31 byte verkey"):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_invalid_checksum_address(xfer_handler, xfer_request):
    operation = xfer_request.operation
    operation[OUTPUTS][0][ADDRESS] = operation[OUTPUTS][0][ADDRESS][:-1] + '1'\
        if '1' != operation[OUTPUTS][0][ADDRESS][-1] else '2'
    with pytest.raises(UnknownIdentifier,
                       match="{} is not a valid base58check value".format(operation[OUTPUTS][0][ADDRESS].encode())):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_invalid_amount(xfer_handler, xfer_request):
    xfer_request.operation[OUTPUTS][0][AMOUNT] = -1
    with pytest.raises(InvalidClientRequest, match="negative or zero value"):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_duplicate_addresses(xfer_handler, xfer_request):
    xfer_request.operation[OUTPUTS].append(xfer_request.operation[OUTPUTS][0])
    with pytest.raises(InvalidClientRequest, match="Each output should contain unique address"):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_no_inputs(xfer_handler, xfer_request):
    del xfer_request.operation[INPUTS]
    with pytest.raises(InvalidClientRequest, match="inputs needs to be present"):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_inputs_and_signatures_do_not_match(xfer_handler, xfer_request):
    xfer_request.operation[INPUTS].clear()
    with pytest.raises(InvalidClientRequest, match="all inputs should have signatures"):
        xfer_handler.static_validation(xfer_request)


@pytest.mark.skip(reason="This behaviour should be expected. We should cut such XFER requests on static validation")
def test_xfer_handler_static_validation_empty_inputs(xfer_handler, xfer_request):
    xfer_request.operation[INPUTS].clear()
    xfer_request.operation["signatures"].clear()
    with pytest.raises(InvalidClientRequest, match="inputs should not be empty"):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_invalid_length_address(xfer_handler, xfer_request):
    operation = xfer_request.operation
    addr = b58encode_check(randomString(31).encode()).decode()
    operation[INPUTS][0][ADDRESS] = addr
    with pytest.raises(InvalidClientRequest, match="Not a valid address as it resolves to 31 byte verkey"):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_invalid_checksum_input_address(xfer_handler, xfer_request):
    operation = xfer_request.operation
    operation[INPUTS][0][ADDRESS] = operation[INPUTS][0][ADDRESS][:-1] + '1' \
        if '1' != operation[INPUTS][0][ADDRESS][-1] else '2'
    with pytest.raises(UnknownIdentifier,
                       match="{} is not a valid base58check value".format(
                           operation[INPUTS][0][ADDRESS].encode())):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_invalid_seq_no(xfer_handler, xfer_request):
    xfer_request.operation[INPUTS][0][SEQNO] = -1
    with pytest.raises(InvalidClientRequest, match="seqNo -- cannot be smaller than 1"):
        xfer_handler.static_validation(xfer_request)


def test_xfer_handler_static_validation_duplicate_input(xfer_handler, xfer_request):
    xfer_request.operation[INPUTS].append(xfer_request.operation[INPUTS][0])
    xfer_request.operation["signatures"].append(xfer_request.operation["signatures"][0])
    with pytest.raises(InvalidClientRequest, match="Each input should be unique"):
        xfer_handler.static_validation(xfer_request)
