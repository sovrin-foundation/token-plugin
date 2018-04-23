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
# TODO This one works
# the operation type is FEES, so the return is a list of fees
def test_authenticate_success():

    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)
    req_data = {'signatures': {'M9BJDuS24bqbJNvBRsoGg3': '2NTMJMnhhZSghbVViTqy2TWoS272kH3apo8ckD4DQf9YXE4zP7g72jg2DLCEzX5ndxUzHmU74hNPjD3syZ8LuBko',
                               'B8fV7naUqLATYocqu7yZ8W': '45rSNuKmfGmitsS2jRJaALkGBWDtXSfuuMdLzLkKUL8AS3xk8f4dM6oKDHvMLnGqVsqmd5z5NDvskj5XmwazrBFP',
                               'CA4bVFDU4GLbX8xZju811o': '4WypVGy9PFKeUio5jAKcGJmsrpnVer9ekm6P2QmN15uRRVeKZux3LzWJ34b4UCdGQEhh7LEv8RbxTXj8Ah8keRBG',
                               'E7QRhdcnhAwA6E46k9EtZo': '5edfnbZLDrz3QaEeuDp9KVMty9agHJpgeWY1PWHSToLfNqSqYrndsUqfbusPymYKRVojvT9uA65ye3bwioQcbMdi'},
                'reqId': 1524252730845898,
                'operation': {'type': '20000', 'fees': {'1': 4, '10001': 8}}
                }

    req_data = {'signatures': {'M9BJDuS24bqbJNvBRsoGg3': '2NTMJMnhhZSghbVViTqy2TWoS272kH3apo8ckD4DQf9YXE4zP7g72jg2DLCEzX5ndxUzHmU74hNPjD3syZ8LuBko'},
                'reqId': 1524252730845898,
                'operation': {'type': '20000', 'fees': {'1': 4, '10001': 8}}
                }
    value = fees_authenticator.authenticate(req_data)
    assert value is not None


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

