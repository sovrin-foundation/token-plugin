import pytest

from plenum.common.constants import DOMAIN_LEDGER_ID, TXN_TYPE
from plenum.common.exceptions import UnknownIdentifier, InvalidSignatureFormat, InsufficientCorrectSignatures
from plenum.server.plugin.token.src.client_authnr import TokenAuthNr
from plenum.server.plugin.token.src.constants import XFER_PUBLIC, MINT_PUBLIC, GET_UTXO, \
    INPUTS, OUTPUTS, ADDRESSES, EXTRA
from plenum.common.request import Request
from plenum.common.types import f, OPERATION

# -------------------------VALID TEST CONSTANTS-------------------------------------------------------------------------
VALID_ADDR_1 = '6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1'
VALID_ADDR_2 = '8kjqqnF3m6agp9auU7k4TWAhuGygFAgPzbNH3shp4HFL'
VALID_ADDR_3 = '2LWr7i8bsnE3BgX7MNUNEBpiJYjn7uEA1HNyMSJyy59z'
VALID_ADDR_4 = 'Dy7AxfksXZELTSxF1sUnEocJAJp98E6taMZ9hhLeDtZH'
VALID_ADDR_5 = 'CDe3vTMgns7nXGFwbGkrz24m2VNghmBScdF3QRstF62g'
VALID_ADDR_6 = '62tw4B64yEu7HmJyjMgZ2tE5wgyTtsXTpB7n8VAtfmjL'
VALID_ADDR_7 = 'D2neNhD3mTgN28HKH8qmLBYnaadb9F2GtL5nAzQpkpR6'

VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"
VALID_REQID = 1517423828260117
PROTOCOL_VERSION = 1
SIGNATURES = {
    'M9BJDuS24bqbJNvBRsoGg3': '5eJax8GW8gTRfZzhuta9s7hU2K3dkKpDWGE7SUsMqiRmQ2GzWXxJKaDzcPMKdZWqrA5Kn1vSHFND9oThsjaQLhHy',
    'B8fV7naUqLATYocqu7yZ8W': 'AaGqjqGk67mj3MVua46RiqJ6mq6zoy99VriGvZJbpZekhrtju9k2NQrrJcdnMnps7cBZfFxLwhELnLZnTqfb9Ag',
    'E7QRhdcnhAwA6E46k9EtZo': '2EBZxZ3E2r2ZjCCBwgD6ipnHbskZb4Y4Yqm6haYEsr7hdM1m36yqLFrmNSB7JPqjAsMx6qjw6dWV5sRou1DgiKrM',
    'CA4bVFDU4GLbX8xZju811o': 'YJjXm8vfiy1sD586tecQ2Eh1Q3wFmLodaxctArasW7RNCujPiZa5CurdW5b8dRXMEBdX9YhsDGkahJXUnZaH8SC'}

VALID_OPERATION = {'type': '10000', 'outputs':
    [['8kjqqnF3m6agp9auU7k4TWAhuGygFAgPzbNH3shp4HFL', 60],
     ['6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1', 40]]}


# -------------------------Test authenticate method---------------------------------------------------------------------


def test_authenticate_invalid_signatures(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    INVALID_SIGNATURES = {
        'M9BJDuS24bqbJNvBRsoGg3': 'INVALID_SIG1',
        'B8fV7naUqLATYocqu7yZ8W': 'INVALID_SIG2',
        'E7QRhdcnhAwA6E46k9EtZo': 'INVALID_SIG3',
        'CA4bVFDU4GLbX8xZju811o': 'INVALID_SIG3'}
    req_data = {f.PROTOCOL_VERSION.nm: PROTOCOL_VERSION,
                f.REQ_ID.nm: VALID_REQID,
                f.SIGS.nm: SIGNATURES,
                OPERATION: VALID_OPERATION}
    with pytest.raises(InsufficientCorrectSignatures):
        token_authnr.authenticate(req_data)


def test_authenticate_invalid_signatures1(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    INVALID_SIGNATURES = {
        'M9BJDuS24bqbJNvBRsoGg3': 'INVALID_SIG1',
        'B8fV7naUqLATYocqu7yZ8W': 'INVALID_SIG2',
        'E7QRhdcnhAwA6E46k9EtZo': 'INVALID_SIG3',
        'CA4bVFDU4GLbX8xZju811o': 'INVALID_SIG3'}
    req_data = {f.PROTOCOL_VERSION.nm: PROTOCOL_VERSION,
                f.REQ_ID.nm: VALID_REQID,
                f.SIGS.nm: SIGNATURES,
                OPERATION: VALID_OPERATION}
    with pytest.raises(InsufficientCorrectSignatures):
        token_authnr.authenticate(req_data)


# -------------------------Test authenticate_xfer method----------------------------------------------------------------


def test_authenticate_xfer():
    pass


# -------------------------Test serializeForSig method------------------------------------------------------------------


def test_serializeForSig():
    pass


# -------------------------Test getVerkey method------------------------------------------------------------------------


def test_getVerkey_success(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    ver_key = token_authnr.getVerkey(VALID_IDENTIFIER)
    assert len(ver_key) == 23
    assert ver_key[0] == '~'


def test_getVerkey_43_len_success(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    identifier_43 = '1234567891234567891234567891234567891234567'
    ver_key = token_authnr.getVerkey(identifier_43)
    assert ver_key == identifier_43


def test_getVerkey_44_len_success(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    identifier_44 = '12345678912345678912345678912345678912345678'
    ver_key = token_authnr.getVerkey(identifier_44)
    assert ver_key == identifier_44


def test_getVerkey_invalid_identifier(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    identifier_invalid = 'INVALID_IDENTIFIER'
    with pytest.raises(UnknownIdentifier):
        token_authnr.getVerkey(identifier_invalid)


# -------------------------Test get_xfer_ser_data method----------------------------------------------------------------


def test__get_xfer_ser_data():
    pass


# -------------------------Test get_sigs method-------------------------------------------------------------------------

def test_get_sigs():
    pass
