import pytest
from sovtokenfees.constants import FEES

from plenum.common.exceptions import InvalidClientRequest


def test_set_fees_handler_static_validation(set_fees_handler, set_fees_request):
    set_fees_handler.static_validation(set_fees_request)


def test_set_fees_handler_static_validation_no_fees(set_fees_handler, set_fees_request):
    del set_fees_request.operation[FEES]
    with pytest.raises(InvalidClientRequest, match="missed fields - fees"):
        set_fees_handler.static_validation(set_fees_request)


def test_set_fees_handler_static_validation_negative_fees(set_fees_handler, set_fees_request):
    set_fees_request.operation[FEES]["nym_alias"] = -1
    with pytest.raises(InvalidClientRequest, match="set_fees -- negative value"):
        set_fees_handler.static_validation(set_fees_request)


def test_set_fees_handler_static_validation_empty_alias(set_fees_handler, set_fees_request):
    set_fees_request.operation[FEES][""] = 1
    with pytest.raises(InvalidClientRequest, match="set_fees -- empty string"):
        set_fees_handler.static_validation(set_fees_request)
