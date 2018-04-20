import pytest

from plenum.common.constants import DOMAIN_LEDGER_ID, TXN_TYPE
from plenum.server.plugin.token.src.client_authnr import TokenAuthNr
from plenum.server.plugin.token.src.constants import XFER_PUBLIC, MINT_PUBLIC, GET_UTXO, \
    INPUTS, OUTPUTS, ADDRESSES, EXTRA
from plenum.common.request import Request

#TEST DATA CONSTANTS
VALID_ADDR_1 = '6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1'
VALID_ADDR_2 = '8kjqqnF3m6agp9auU7k4TWAhuGygFAgPzbNH3shp4HFL'
VALID_ADDR_3 = '2LWr7i8bsnE3BgX7MNUNEBpiJYjn7uEA1HNyMSJyy59z'
VALID_ADDR_4 = 'Dy7AxfksXZELTSxF1sUnEocJAJp98E6taMZ9hhLeDtZH'
VALID_ADDR_5 = 'CDe3vTMgns7nXGFwbGkrz24m2VNghmBScdF3QRstF62g'
VALID_ADDR_6 = '62tw4B64yEu7HmJyjMgZ2tE5wgyTtsXTpB7n8VAtfmjL'
VALID_ADDR_7 = 'D2neNhD3mTgN28HKH8qmLBYnaadb9F2GtL5nAzQpkpR6'

VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"
VALID_REQID = 1517423828260117
CONS_TIME = 1518541344
PROTOCOL_VERSION = 1
SIGNATURES = {'B8fV7naUqLATYocqu7yZ8W':
                  '27BVCWvThxMV9pzqz3JepMLVKww7MmreweYjh15LkwvAH4qwYAMbZWeYr6E6LcQexYAikTHo212U1NKtG8Gr2PPP',
              'M9BJDuS24bqbJNvBRsoGg3':
                  '5BzS7J7uSuUePRzLdF5BL5LPvnXxzQyB5BqMT19Hz8QjEyb41Mum71TeNvPW9pKbhnDK12Pciqw9WRHUvsfwdYT5',
              'E7QRhdcnhAwA6E46k9EtZo':
                  'MsZsG2uQHFqMvAsQsx5dnQiqBjvxYS1QsVjqHkbvdS2jPdZQhJfackLQbxQ4RDNUrDBy8Na6yZcKbjK2feun7fg',
              'CA4bVFDU4GLbX8xZju811o':
                  '3A1Pmkox4SzYRavTj9toJtGBr1Jy9JvTTnHz5gkS5dGnY3PhDcsKpQCBfLhYbKqFvpZKaLPGT48LZKzUVY4u78Ki'}

def test_authenticate(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: MINT_PUBLIC,
                                                      OUTPUTS: [[VALID_ADDR_1, 40], [VALID_ADDR_2, 20]],
                                                      INPUTS: [[VALID_ADDR_2, 1, '']]}, None, SIGNATURES, 1)


def test_authenticate_xfer():
    pass

def test_serializeForSig():
    pass

def test_getVerkey():
    pass

def test__get_xfer_ser_data():
    pass

def test_get_sigs():
    pass
