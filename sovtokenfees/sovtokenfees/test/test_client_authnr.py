import pytest

from sovtokenfees.client_authnr import FeesAuthNr
from sovtoken.constants import AMOUNT, SEQNO, ADDRESS
from plenum.common.exceptions import InvalidSignatureFormat, \
    InsufficientCorrectSignatures, InvalidClientRequest
from plenum.common.constants import DOMAIN_LEDGER_ID
from state.pruning_state import PruningState
from storage.kv_in_memory import KeyValueStorageInMemory

VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"
VALID_REQID = 1517423828260117
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

    @property
    def digest(self):
        return "5b87c6c6f36df259af3682abdee5ce072941186b8f03abde24ee362a19f5b5b5"


# ------------------------------------------------------------------------------------
# creates state instance that will be good enough for some of the test below
def pruning_state():
    return PruningState(KeyValueStorageInMemory())


# ------------------------------------------------------------------------------------
# gets nodes properly setup, required for some of the test
@pytest.fixture
def node(txnPoolNodeSet):
    a, b, c, d = txnPoolNodeSet
    nodes = [a, b, c, d]
    return nodes


# ------------------------------------------------------------------------------------
# authenticate returns a list of authenticated signatures.  it should match the number
# of inputted signatures since they are all valid
def test_authenticate_success(node):

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
# similar to the previous success test, authenticate returns a list of authenticated signatures.  it should match the number
# of inputted signatures since they are all valid
def test_authenticate_success_one_signature(node):

    state = node[0].getState(DOMAIN_LEDGER_ID)
    fees_authenticator = FeesAuthNr(state, None)

    req_data = {
        'signatures':
            {
                'E7QRhdcnhAwA6E46k9EtZo': '32H37GfuchojdbNeMxwNUhZJwWyJCz48aP5u1AvN3xhNramVqrq74H4pE8LKMgZw7rAdyrPvHUWzWAZdB243fqhA'
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
    assert 1 == len(value)

# ------------------------------------------------------------------------------------
# only 2 of the 4 signatures are valid.  (hint: the last two are mucky)
def test_authenticate_errors_on_invalid_inputs(node):

    state = node[0].getState(DOMAIN_LEDGER_ID)
    fees_authenticator = FeesAuthNr(state, None)

    req_data = {
        'signatures':
            {
                'E7QRhdcnhAwA6E46k9EtZo': '32H37GfuchojdbNeMxwNUhZJwWyJCz48aP5u1AvN3xhNramVqrq74H4pE8LKMgZw7rAdyrPvHUWzWAZdB243fqhA',
                'CA4bVFDU4GLbX8xZju811o': '3tkZU65KeybmkUcrA6HuovVTDD8vsVm2VvB7bpUhPt2MLpez6eRrRvysUutusJz6xryCtk7g1b115pKhNGcqRTss',
                'M9BJDuS24bqbJNvBRsoGg3': '00XHdWTeWYRpoyCAZgpM7qA7Ms2MRYu6NpasPagPQRGoUukE2NdSXGonu6dWgsPNgybqW7fotw9BjccXAy7BzMsY',
                'B8fV7naUqLATYocqu7yZ8W': '00q55hTSBafovXS9gTNkW1GM9vVF6Y4s2fLEsmew9DaN95rmZ5ZwXj74NgTmGeGszPomWXPsRr5QGNZb6GsG57PV'
            },
        'reqId': 1524500821797147,
        'operation':
            {
                'fees': {'10001': 8, '1': 4},
                'type': '20000'
            },
        'protocolVersion': 1
    }

    with pytest.raises(InvalidSignatureFormat):
        fees_authenticator.authenticate(req_data)


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
    msg.signatures = {'V4SGRU86Z58d6TV7PBUe6f': 'dYZZFV6Fk59bFaNFaKwXfY9AqP6cr3wqTSPjoRLoLcgAi28RNErweRXRskzZ4cwRyzBCpZyzewmSPdrQb1oES83'}

    #                                 1         2         3         4   4
    #                        12345678901234567890123456789012345678901234567890
    inputs = [{ADDRESS: '2gWVuNmy8rdJrDHzQ9PDDpHkfcypyUZRsSHaqA9q1K3Gti3YXw', SEQNO: 153}]
    outputs = [{ADDRESS: '2gWVuNmy8rdJrDHzQ9PDDpHkfcypyUZRsSHaqA9q1K3Gti3YXw', AMOUNT: 9}]
    signatures = ['5cEsNP3tfVLG5hdKfW5dCNVyM6gtoUAgGDsTUsikfNw6ZEJXme4v6KxZPP6wvniwg6FZbeTMtkcQ5TY4uf3ihWsG']
    setattr(msg, "fees", [inputs, outputs, signatures])

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

    inputs = [{ADDRESS: '2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es', SEQNO: 2}]
    outputs = [{ADDRESS: '2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es', AMOUNT: 10}]
    signatures = ['000kKoLEAP1YCYULYqxSNKvcYigGG1fHRMbZ6N1byFhaRut4P5RDF2KGR73ffgQoyzMHabrcTvrRGHhEfQ6ZdzxB']
    setattr(msg, "fees", [inputs, outputs, signatures
    ])

    with pytest.raises(InvalidSignatureFormat):
        fees_authenticator.verify_signature(msg)


# ------------------------------------------------------------------------------------
# in this test, the signature in fees is not valid for the data set.  it is a valid signature and passes b58decode
def test_verify_signature_incorrect_signatures():
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)
    msg = FeeData()
    msg.signatures = {'MSjKTWkPLtYoPEaTF1TUDb': '61PUc8K8aAkhmCjWLstxwRREBAJKbVMRuGiUXxSo1tiRwXgUfVT4TY47NJtbQymcDW3paXPWNqqD4cziJjoPQSSX'}

    inputs = [{ADDRESS: '2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es', SEQNO: 2}]
    outputs = [{ADDRESS: '2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es', AMOUNT: 10}]
    signatures = ['5wuXGeWyrM2xcp68rRsYEaegaguEJBBTDQioeSgDv5jMFeaeSLPAcMs4XwcxNXBwoUAUWgxSMN9WUnZ7ADctdPyQ']
    setattr(msg, "fees", [inputs, outputs, signatures])

    with pytest.raises(InsufficientCorrectSignatures):
        fees_authenticator.verify_signature(msg)


# ------------------------------------------------------------------------------------
# fees sections are populated with correct data
# however the signature is not signed for all of the values
def test_verify_signature_mismatch_of_signatures():
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)

    msg = FeeData()
    msg.signatures = {'MSjKTWkPLtYoPEaTF1TUDb': '61PUc8K8aAkhmCjWLstxwRREBAJKbVMRuGiUXxSo1tiRwXgUfVT4TY47NJtbQymcDW3paXPWNqqD4cziJjoPQSSX'}

    #                                 1         2         3         4   4
    #                        12345678901234567890123456789012345678901234567890
    address = '2JMyZgFBFyp5YMsBta4gCFA5TMdUzMXrWbRvMFkW7KDNbaMrk1'
    inputs = [
        {ADDRESS: address, SEQNO: 1},
        {ADDRESS: address, SEQNO: 1}
    ]
    outputs = [
        {ADDRESS: address, AMOUNT: 4},
        {ADDRESS: address, AMOUNT: 5},
    ]
    signatures = ['2z34R9vCyohVS2V7SXf8VnkHuAm8a224D6hopKJBMbdV4z8meR8aTdLMbMiknRXnKD4YkGtZnYY1D6jSQz23FziG']
    setattr(msg, "fees", [inputs, outputs, signatures])

    with pytest.raises(InsufficientCorrectSignatures):
        fees_authenticator.verify_signature(msg)


# ------------------------------------------------------------------------------------
# the signature and fees sections are populated with correct data but the sequence
# number is wrong.
def test_verify_signature_sequence_order_wrong():
    state = pruning_state()
    fees_authenticator = FeesAuthNr(state, None)

    msg = FeeData()
    msg.signatures = {'MSjKTWkPLtYoPEaTF1TUDb': '61PUc8K8aAkhmCjWLstxwRREBAJKbVMRuGiUXxSo1tiRwXgUfVT4TY47NJtbQymcDW3paXPWNqqD4cziJjoPQSSX'}

    #                                 1         2         3         4   4
    #                        12345678901234567890123456789012345678901234567890
    address = '2JMyZgFBFyp5YMsBta4gCFA5TMdUzMXrWbRvMFkW7KDNbaMrk1'
    inputs = [{ADDRESS: address, SEQNO: 2}]
    outputs = [{ADDRESS: address, AMOUNT: 9}]
    signatures = ['2z34R9vCyohVS2V7SXf8VnkHuAm8a224D6hopKJBMbdV4z8meR8aTdLMbMiknRXnKD4YkGtZnYY1D6jSQz23FziG']
    setattr(msg, "fees", [inputs, outputs, signatures])

    with pytest.raises(InsufficientCorrectSignatures):
        fees_authenticator.verify_signature(msg)