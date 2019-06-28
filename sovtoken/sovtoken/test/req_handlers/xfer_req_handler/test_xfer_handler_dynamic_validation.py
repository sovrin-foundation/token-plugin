import pytest
from sovtoken.exceptions import InsufficientFundsError, ExtraFundsError, InvalidFundsError


def test_xfer_handler_dynamic_validation_valid(xfer_handler, xfer_request):
    xfer_handler.dynamic_validation(xfer_request)


def test_xfer_handler_dynamic_validation_insufficient_funds(xfer_handler, invalid_amount_xfer_request_insufficient):
    with pytest.raises(InsufficientFundsError,
                       match='Insufficient funds, sum of inputs is 10but required amount is 11. sum of outputs: 11'):
        xfer_handler.dynamic_validation(invalid_amount_xfer_request_insufficient)


def test_xfer_handler_dynamic_validation_excessive(xfer_handler, invalid_amount_xfer_request_excessive):
    with pytest.raises(ExtraFundsError,
                       match="Extra funds, sum of inputs is 10 but required amount: 9 -- sum of outputs: 9"):
        xfer_handler.dynamic_validation(invalid_amount_xfer_request_excessive)


def test_xfer_handler_dynamic_validation_utxo_not_exists(xfer_handler, invalid_amount_xfer_request_utxo_does_not_exist,
                                                         payment_address):
    with pytest.raises(InvalidFundsError,
                       message="InvalidFundsError(\"seq_nos {{2}} are not found in list of seq_nos_amounts for "
                               "address {} -- current list: ['1', '10']\",)".format(payment_address[8:])):
        xfer_handler.dynamic_validation(invalid_amount_xfer_request_utxo_does_not_exist)
