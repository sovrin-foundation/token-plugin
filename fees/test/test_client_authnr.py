import pytest
import json

from plenum.server.plugin.fees.src.client_authnr import FeesAuthNr
from plenum.common.exceptions import InvalidSignatureFormat, \
    InsufficientCorrectSignatures, InvalidClientRequest
from plenum.common.constants import DOMAIN_LEDGER_ID

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
SIGNATURES = {'B8fV7naUqLATYocqu7yZ8W':
                  '27BVCWvThxMV9pzqz3JepMLVKww7MmreweYjh15LkwvAH4qwYAMbZWeYr6E6LcQexYAikTHo212U1NKtG8Gr2PPP',
              'M9BJDuS24bqbJNvBRsoGg3':
                  '5BzS7J7uSuUePRzLdF5BL5LPvnXxzQyB5BqMT19Hz8QjEyb41Mum71TeNvPW9pKbhnDK12Pciqw9WRHUvsfwdYT5',
              'E7QRhdcnhAwA6E46k9EtZo':
                  'MsZsG2uQHFqMvAsQsx5dnQiqBjvxYS1QsVjqHkbvdS2jPdZQhJfackLQbxQ4RDNUrDBy8Na6yZcKbjK2feun7fg',
              'CA4bVFDU4GLbX8xZju811o':
                  '3A1Pmkox4SzYRavTj9toJtGBr1Jy9JvTTnHz5gkS5dGnY3PhDcsKpQCBfLhYbKqFvpZKaLPGT48LZKzUVY4u78Ki'}


# ------------------------------------------------------------------------------------
# this class is used to help build up fees data for testing
class FeeData:
    def __init__(self):
        self.protocolVersion = PROTOCOL_VERSION
        self.reqId = VALID_REQID
        self.identifier = VALID_IDENTIFIER

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
# TODO This one works
# the operation type is FEES, so the return is a list of fees
def test_authenticate_success():
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)
    req_data = {'signatures': SIGNATURES,
                'reqId': VALID_REQID,
                'identifier': VALID_IDENTIFIER,
                'operation': {'type': SET_FEES,
                              'fees': {'1': 4, '10001': 8}
                              }
                }

    value = fees_authenticator.authenticate(req_data)
    assert value is not None


# ------------------------------------------------------------------------------------
# This one works
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
# This one works
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
# This one works
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
# this one works....
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
# TODO this one works
#
def test_verify_signature_incorrect_signatures():
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)
    msg = FeeData()
    msg.signatures = {'MSjKTWkPLtYoPEaTF1TUDb': '61PUc8K8aAkhmCjWLstxwRREBAJKbVMRuGiUXxSo1tiRwXgUfVT4TY47NJtbQymcDW3paXPWNqqD4cziJjoPQSSX'}

    setattr(msg, "fees", [[['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 2, 'C4xbW4SRLA8MaBpPfWrHvuoN6VEb8tzc21a2WMYfVGGTjK7KhUBAQaQ36iGqekDxbWuuVdZTu2PE47weiMUrH6E']],
                           ['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 10]])

    with pytest.raises(InsufficientCorrectSignatures):
        fees_authenticator.verify_signature(msg)

