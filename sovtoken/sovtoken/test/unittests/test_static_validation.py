import pytest

from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import InvalidClientRequest
from plenum.common.request import Request


# TEST CONSTANTS
from sovtoken.constants import XFER_PUBLIC, MINT_PUBLIC, SIGS, \
    OUTPUTS, INPUTS, GET_UTXO, ADDRESS
from sovtoken.messages.txn_validator import txn_xfer_public_validate, txt_get_utxo_validate, txn_mint_public_validate
from sovtoken.test.constants import VALID_IDENTIFIER, VALID_REQID, SIGNATURES, VALID_ADDR_1, VALID_ADDR_2


def test_MINT_PUBLIC_validate_success():
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: MINT_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 40
                                                      }]},
                      None, SIGNATURES, 1)
    ret_val = txn_mint_public_validate(request)
    assert ret_val is None


def test_MINT_PUBLIC_validate_missing_output():
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: MINT_PUBLIC},
                      None, SIGNATURES, 1)
    with pytest.raises(InvalidClientRequest):
        txn_mint_public_validate(request)


def test_XFER_PUBLIC_validate_success():
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 20
                                                      }],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "seqNo": 1
                                                      }],
                                                      SIGS: ['']}, None, SIGNATURES, 1)
    ret_val = txn_xfer_public_validate(request)
    assert ret_val is None

def test_XFER_PUBLIC_validate_missing_output():
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC, INPUTS: [{"address": VALID_ADDR_2, "seqNo": 1}]},
                      None, SIGNATURES, 1)
    with pytest.raises(InvalidClientRequest):
        txn_xfer_public_validate(request)


def test_XFER_PUBLIC_validate_missing_input():
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 20
                                                      }]},
                      None, SIGNATURES, 1)
    with pytest.raises(InvalidClientRequest):
        txn_xfer_public_validate(request)


def test_GET_UTXO_validate_missing_address():
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: GET_UTXO},
                      None, SIGNATURES, 1)
    with pytest.raises(InvalidClientRequest):
        txt_get_utxo_validate(request)


def test_GET_UTXO_validate_success():
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: GET_UTXO,
                                                      ADDRESS: VALID_ADDR_1},
                      None, SIGNATURES, 1)
    ret_val = txt_get_utxo_validate(request)
    assert ret_val is None