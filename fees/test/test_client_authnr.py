import pytest
import json

from plenum.server.plugin.fees.src.client_authnr import FeesAuthNr
from plenum.common.exceptions import InvalidSignatureFormat, \
    InsufficientCorrectSignatures, InvalidClientRequest
from plenum.common.constants import DOMAIN_LEDGER_ID

from plenum.server.plugin.fees.test.test_set_get_fees import fees_set

# Constants
from plenum.server.plugin.fees.src.constants import SET_FEES
from plenum.server.plugin.token.src.client_authnr import TokenAuthNr
from state.state import State
from state.pruning_state import PruningState
from storage.kv_in_memory import KeyValueStorageInMemory

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
SIGNATURES = {'M9BJDuS24bqbJNvBRsoGg3': '5eJax8GW8gTRfZzhuta9s7hU2K3dkKpDWGE7SUsMqiRmQ2GzWXxJKaDzcPMKdZWqrA5Kn1vSHFND9oThsjaQLhHy',
              'B8fV7naUqLATYocqu7yZ8W': 'AaGqjqGk67mj3MVua46RiqJ6mq6zoy99VriGvZJbpZekhrtju9k2NQrrJcdnMnps7cBZfFxLwhELnLZnTqfb9Ag',
              'E7QRhdcnhAwA6E46k9EtZo': '2EBZxZ3E2r2ZjCCBwgD6ipnHbskZb4Y4Yqm6haYEsr7hdM1m36yqLFrmNSB7JPqjAsMx6qjw6dWV5sRou1DgiKrM',
              'CA4bVFDU4GLbX8xZju811o': 'YJjXm8vfiy1sD586tecQ2Eh1Q3wFmLodaxctArasW7RNCujPiZa5CurdW5b8dRXMEBdX9YhsDGkahJXUnZaH8SC'}


# ------------------------------------------------------------------------------------
# this class is used to help build up fees data for testing
class FeeData:
    def __init__(self):
        self.protocolVersion = PROTOCOL_VERSION
        self.reqId = VALID_REQID
        self.identifier = VALID_IDENTIFIER
        self.signatures = SIGNATURES

    pass


# ------------------------------------------------------------------------------------
# helper method for creating a state instance which will support the functions
# of the test
def pruning_state():
    return PruningState(KeyValueStorageInMemory())


# ------------------------------------------------------------------------------------
# test fixtures
@pytest.fixture
def node(txnPoolNodeSet):
    a, b, c, d = txnPoolNodeSet
    nodes = [a, b, c, d]
    return nodes


# ------------------------------------------------------------------------------------
# authenticate returns a list of authenticated signatures.  it should match the number
# of inputted signatures since they are all valie
def test_authenticate_success(fees_set, node):

    state = node[0].getState(DOMAIN_LEDGER_ID)
    fees_authenticator = FeesAuthNr(state, None)

    req_data = {
        'signatures':
            {
                'E7QRhdcnhAwA6E46k9EtZo': '32H37GfuchojdbNeMxwNUhZJwWyJCz48aP5u1AvN3xhNramVqrq74H4pE8LKMgZw7rAdyrPvHUWzWAZdB243fqhA',
                'CA4bVFDU4GLbX8xZju811o': '3tkZU65KeybmkUcrA6HuovVTDD8vsVm2VvB7bpUhPt2MLpez6eRrRvysUutusJz6xryCtk7g1b115pKhNGcqRTss',
                'M9BJDuS24bqbJNvBRsoGg3': '4QXHdWTeWYRpoyCAZgpM7qA7Ms2MRYu6NpasPagPQRGoUukE2NdSXGonu6dWgsPNgybqW7fotw9BjccXAy7BzMsY',
                'B8fV7naUqLATYocqu7yZ8W': '2bq55hTSBafovXS9gTNkW1GM9vVF6Y4s2fLEsmew9DaN95rmZ5ZwXj74NgTmGeGszPomWXPsRr5QGNZb6GsG57PV'
            },
        'reqId': 1524500821797147,
        'operation':
            {
                'fees': {'10001': 8, '1': 4},
                'type': '20000'
            },
        'protocolVersion': 1
    }

    value = fees_authenticator.authenticate(req_data)
    assert value is not None
    assert 4 == len(value)


# ------------------------------------------------------------------------------------
# the operation type is not FEES so the exception InvalidClientRequest is raised
def test_authenticate_invalid():
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)
    req_data = {'signatures': SIGNATURES, 'reqId': VALID_REQID,
                'operation': {'type': 'INVALID_TXN_TYPE',
                              'fees': {'1': 4, '10001': 8}
                              }
                }
    with pytest.raises(InvalidClientRequest):
        fees_authenticator.authenticate(req_data, VALID_IDENTIFIER)


# ------------------------------------------------------------------------------------
# the signature and fees sections are populated with correct data
def test_verify_signature_success():
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)

    msg = FeeData()
    msg.signatures = {'MSjKTWkPLtYoPEaTF1TUDb': '61PUc8K8aAkhmCjWLstxwRREBAJKbVMRuGiUXxSo1tiRwXgUfVT4TY47NJtbQymcDW3paXPWNqqD4cziJjoPQSSX'}

    setattr(msg, "fees", [[['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 2, 'C4xbW4SRLA8MaBpPfWrHvuoN6VEb8tzc21a2WMYfVGGTjK7KhUBAQaQ36iGqekDxbWuuVdZTu2PE47weiMUrH6E']],
                           ['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 10]])

    fees_authenticator.verify_signature(msg)


# ------------------------------------------------------------------------------------
# Its pretty simple.  If verify_signature doesn't find a fee attribute, it just
# returns, no return results and no exceptions
def test_verify_signature_no_fees():
    # should just run, no exceptions
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)
    msg = FeeData()
    msg.signatures = {'MSjKTWkPLtYoPEaTF1TUDb': '61PUc8K8aAkhmCjWLstxwRREBAJKbVMRuGiUXxSo1tiRwXgUfVT4TY47NJtbQymcDW3paXPWNqqD4cziJjoPQSSX'}

    fees_authenticator.verify_signature(msg)


# ------------------------------------------------------------------------------------
# in the fees dictionary, array in element 0 has a signature that is not correct so the
# exception InvalidSignatureFormat will get raised
def test_verify_signature_invalid_signature_format(node):
    fees_authenticator = FeesAuthNr(node[0].getState(DOMAIN_LEDGER_ID), None)
    msg = FeeData()
    msg.signatures = {'MSjKTWkPLtYoPEaTF1TUDb': '61PUc8K8aAkhmCjWLstxwRREBAJKbVMRuGiUXxSo1tiRwXgUfVT4TY47NJtbQymcDW3paXPWNqqD4cziJjoPQSSX'}

    setattr(msg, "fees", [[['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 2, '000bW4SRLA8MaBpPfWrHvuoN6VEb8tzc21a2WMYfVGGTjK7KhUBAQaQ36iGqekDxbWuuVdZTu2PE47weiMUrH6E']],
                           ['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 10]])
    with pytest.raises(InvalidSignatureFormat):
        fees_authenticator.verify_signature(msg)


# ------------------------------------------------------------------------------------
# in this test, the signature in fees is not valid for the data set.  it is a valid signature and passes b58decode
def test_verify_signature_incorrect_signatures():
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)
    msg = FeeData()
    msg.signatures = {'MSjKTWkPLtYoPEaTF1TUDb': '61PUc8K8aAkhmCjWLstxwRREBAJKbVMRuGiUXxSo1tiRwXgUfVT4TY47NJtbQymcDW3paXPWNqqD4cziJjoPQSSX'}

    setattr(msg, "fees", [[['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 2, '5wuXGeWyrM2xcp68rRsYEaegaguEJBBTDQioeSgDv5jMFeaeSLPAcMs4XwcxNXBwoUAUWgxSMN9WUnZ7ADctdPyQ']],
                           ['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 10]])

    with pytest.raises(InsufficientCorrectSignatures):
        fees_authenticator.verify_signature(msg)

