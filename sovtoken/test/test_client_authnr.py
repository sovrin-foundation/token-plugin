import pytest
import mock

from plenum.common.constants import DOMAIN_LEDGER_ID
from plenum.common.exceptions import UnknownIdentifier, InvalidSignatureFormat, InsufficientCorrectSignatures, \
    CouldNotAuthenticate
from plenum.server.client_authn import CoreAuthNr
from plenum.server.plugin.sovtoken.src.wallet import TokenWallet
from plenum.server.plugin.sovtoken.src.client_authnr import TokenAuthNr, AddressSigVerifier
from plenum.server.plugin.sovtoken.src.constants import INPUTS, OUTPUTS, EXTRA
from plenum.common.types import f, OPERATION
from plenum.server.plugin.sovtoken.test.helper import public_mint_request, \
    xfer_request


# -------------------------Class fixtures-------------------------------------------------------------------------------


@pytest.fixture
def node(txnPoolNodeSet):
    a, b, c, d = txnPoolNodeSet
    nodes = [a, b, c, d]
    return nodes


@pytest.fixture(scope="function")
def user1_token_wallet():
    return TokenWallet('user1')


@pytest.fixture(scope="function")
def user2_token_wallet():
    return TokenWallet('user2')


@pytest.fixture(scope="function")
def SF_token_wallet():
    return TokenWallet('SF_MASTER')


@pytest.fixture(scope="function")
def user1_address(user1_token_wallet):
    seed = 'user1000000000000000000000000000'.encode()
    user1_token_wallet.add_new_address(seed=seed)
    return next(iter(user1_token_wallet.addresses.keys()))


@pytest.fixture(scope="function")
def user2_address(user2_token_wallet):
    seed = 'user2000000000000000000000000000'.encode()
    user2_token_wallet.add_new_address(seed=seed)
    return next(iter(user2_token_wallet.addresses.keys()))


@pytest.fixture(scope="function")
def SF_address(SF_token_wallet):
    seed = 'sf000000000000000000000000000000'.encode()
    SF_token_wallet.add_new_address(seed=seed)
    return next(iter(SF_token_wallet.addresses.keys()))


# -------------------------VALID TEST CONSTANTS-------------------------------------------------------------------------

# this valid identifier represents a DID that submitted the transaction
VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"

# Unique ID number of the request with transaction
VALID_REQID = 1524769177045798
VALID_XFER_REQID = 1525070057872273

# The version of client-to-node protocol.
PROTOCOL_VERSION = 1

# -------------------------Test AddressSigVerifier.verify method--------------------------------------------------------

# This test verifies that the sig param is the signature of the message given the verKey
# The hardcoded values come from running test_authenticate_xfer_success() in debug mode
def test_verify_success(node, user2_token_wallet, user2_address, user1_address):
    addressSigVerifier_obj = AddressSigVerifier('AU8FgXMZtGMhua4g1e6J8c1sZx7Mp1yk6B69M3yCUsUw')
    sig = b'w\xab\xc9\xaf\xbe\xba\xbaQ\xcac\x06:M\xc3)\xae\xd8\xa4\xf8\xb2;\xc9<C\xff\xc6\xc5i\xf1o\xf2\x87\xd4\xae' \
          b'\xce\x95\xf4$\xfa\x92\xd6\xa7\xf6\x0b\x19@Q\xdd\xe7\x1a\xccArJ\xcaC\xb9]\xa0\x12\xa9\xb1y\x0b'
    msg = b'identifier:24xHHVDRq97Hss5BxiTciEDsve7nYNx1pxAMi9RAvcWMouviSY|operation:extra:|inputs:24xHHVDRq97Hss5Bx' \
          b'iTciEDsve7nYNx1pxAMi9RAvcWMouviSY,1|outputs:2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es,10,24xHH' \
          b'VDRq97Hss5BxiTciEDsve7nYNx1pxAMi9RAvcWMouviSY,10|type:10001|reqId:1525258251652534'
    assert True == addressSigVerifier_obj.verify(sig, msg)

# This test that the verKey can't verify the signature. The hardcoded values come from debug mode of running
# The hardcoded values come from running test_authenticate_xfer_insufficient_correct_signatures() in debug mode
def test_verify_fail():
    addressSigVerifier_obj = AddressSigVerifier('AU8FgXMZtGMhua4g1e6J8c1sZx7Mp1yk6B69M3yCUsUw')
    sig = b"J\x97v\x10\tp\x0c9R\xcc\xfd\xc6\xfa\x9a\xca\xef\xf0\xfe'\xb2Gfg\xe0w\xa6\x1e\xc5*\x83\xea\x130\\\xa3T\n" \
          b"\xb3\x12`\xf9)^[\x9d\x887\xa6\x87A,\x19\xdc\x1b\xdc\xb5S#9^\x12Yk\x0e"
    ser_data = b'identifier:24xHHVDRq97Hss5BxiTciEDsve7nYNx1pxAMi9RAvcWMouviSY|operation:extra:|inputs:24xHHVDRq97H' \
               b'ss5BxiTciEDsve7nYNx1pxAMi9RAvcWMouviSY,2|outputs:2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7E' \
               b's,10,24xHHVDRq97Hss5BxiTciEDsve7nYNx1pxAMi9RAvcWMouviSY,10|type:10001|reqId:1525258344537237'
    assert False == addressSigVerifier_obj.verify(sig, ser_data)

# -------------------------Test authenticate method---------------------------------------------------------------------

# This test is used to check that invalid signatures are throwing an InsufficientCorrectSignatures exception
def test_authenticate_invalid_signatures_format(node, trustee_wallets, SF_address, user1_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    outputs = [[SF_address, 30], [user1_address, 30]]
    request = public_mint_request(trustee_wallets, outputs)
    req_data = request.as_dict
    req_data[f.SIGS.nm] = {
        'M9BJDuS24bqbJNvBRsoGg3': 'INVALID_SIG1',
        'B8fV7naUqLATYocqu7yZ8W': 'INVALID_SIG2',
        'E7QRhdcnhAwA6E46k9EtZo': 'INVALID_SIG3',
        'CA4bVFDU4GLbX8xZju811o': 'INVALID_SIG3'}
    with pytest.raises(InvalidSignatureFormat):
        token_authnr.authenticate(req_data)


# This test is to validate properly formed invalid signatures are throwing an InsufficientCorrectSignatures
def test_authenticate_insufficient_valid_signatures_data(node, trustee_wallets, SF_address, user1_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    outputs = [[SF_address, 30], [user1_address, 30]]
    request = public_mint_request(trustee_wallets, outputs)
    req_data = request.as_dict
    req_data[f.SIGS.nm]['E7QRhdcnhAwA6E46k9EtZo'] = \
        '2EBZxZ3E2r2ZjCCBwgD6ipnHbskZb4Y4Yqm6haYEsr7hdM1m36yqLFrmNSB7JPqjAsMx6qjw6dWV5sRou1DgiKrM'
    with pytest.raises(InsufficientCorrectSignatures):
        token_authnr.authenticate(req_data)


# This test is checking to make sure a threshold of correct signatures is met
def test_authenticate_success_4_sigs(node, trustee_wallets, SF_address, user1_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    outputs = [[SF_address, 30], [user1_address, 30]]
    request = public_mint_request(trustee_wallets, outputs)
    req_data = request.as_dict
    correct_sigs = token_authnr.authenticate(req_data)
    assert len(correct_sigs) == 4


# This test is used to verify that authenticate_xfer is called with a XFER_PUBLIC type is given
@mock.patch.object(TokenAuthNr, 'authenticate_xfer', return_value=True)
def test_authenticate_calls_authenticate_xfer(node, user2_token_wallet, user1_address, user2_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    inputs = [[user2_token_wallet, user2_address, 1]]
    outputs = [[user1_address, 10], [user2_address, 10]]
    request = xfer_request(inputs, outputs)
    req_data = request.__dict__
    monkeypatch_val = token_authnr.authenticate(req_data)
    assert monkeypatch_val == True


# -------------------------Test authenticate_xfer method----------------------------------------------------------------

# This test verifies that authenticate_xfer verifies the signatures and returns data to represent this
def test_authenticate_xfer_success(node, user2_token_wallet, user2_address, user1_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    inputs = [[user2_token_wallet, user2_address, 1]]
    outputs = [[user1_address, 10], [user2_address, 10]]
    request = xfer_request(inputs, outputs)
    req_data = request.as_dict
    correct_sigs = token_authnr.authenticate_xfer(req_data, AddressSigVerifier)
    assert len(correct_sigs) == 1


# This test verifies that authenticate_xfer raises an error when an invalid formatted signature is submitted
def test_authenticate_xfer_invalid_signature_format(node, user2_token_wallet, user2_address, user1_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    inputs = [[user2_token_wallet, user2_address, 1]]
    outputs = [[user1_address, 10], [user2_address, 10]]
    request = xfer_request(inputs, outputs)
    req_data = request.as_dict
    req_data[OPERATION]["signatures"][0] =  'INVALID_SIGNATURE'
    with pytest.raises(InvalidSignatureFormat):
        token_authnr.authenticate_xfer(req_data, AddressSigVerifier)


# This test verifies that authenticate_xfer raises an error when an invalid formatted signature is submitted
@mock.patch.object(TokenAuthNr, 'getVerkey', return_value=None)
def test_authenticate_xfer_could_not_authenticate(node, user2_token_wallet, user2_address, user1_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    inputs = [[user2_token_wallet, user2_address, 1]]
    outputs = [[user1_address, 10], [user2_address, 10]]
    request = xfer_request(inputs, outputs)
    req_data = request.as_dict
    with pytest.raises(CouldNotAuthenticate):
        token_authnr.authenticate_xfer(req_data, AddressSigVerifier)


# This test is intended to determine that authenticate_xfer raises an error if all sigantures are not valid
def test_authenticate_xfer_insufficient_correct_signatures(node, user2_token_wallet, user2_address, user1_address,
                                                           SF_address, SF_token_wallet):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    inputs = [[user2_token_wallet, user2_address, 1], [SF_token_wallet, SF_address, 2]]
    outputs = [[user1_address, 10], [user2_address, 10]]
    request = xfer_request(inputs, outputs)
    req_data = request.as_dict

    # creating invalid signature in index 0
    req_data[OPERATION]["signatures"][0] = req_data[OPERATION]["signatures"][1]
    with pytest.raises(InsufficientCorrectSignatures):
        token_authnr.authenticate_xfer(req_data, AddressSigVerifier)


# -------------------------Test serializeForSig method------------------------------------------------------------------

# This test that the serializeForSig method is being called when a XFER_PUBLIC request is submitted
@mock.patch.object(CoreAuthNr, 'serializeForSig', return_value=True)
def test_serializeForSig_XFER_PUBLIC_path(node, user2_token_wallet, user2_address,
                                          SF_token_wallet, SF_address, user1_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    inputs = [[user2_token_wallet, user2_address, 1], [SF_token_wallet, SF_address, 2]]
    outputs = [[user1_address, 10], [user1_address, 10]]
    request = xfer_request(inputs, outputs)
    msg = request.as_dict
    serialize_for_sig_called = token_authnr.serializeForSig(msg, VALID_IDENTIFIER, None)
    assert serialize_for_sig_called == True


# This test that the serializeForSig method is being called when a MINT_PUBLIC request is submitted
@mock.patch.object(CoreAuthNr, 'serializeForSig', return_value=True)
def test_serializeForSig_MINT_PUBLIC_path(node, SF_address, user1_address, trustee_wallets):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    outputs = [[SF_address, 30], [user1_address, 30]]
    request = public_mint_request(trustee_wallets, outputs)
    msg = request.as_dict
    serialize_for_sig_called = token_authnr.serializeForSig(msg, VALID_IDENTIFIER, None)
    assert serialize_for_sig_called == True


# -------------------------Test getVerkey method------------------------------------------------------------------------


# This tests that a valid verkey of a DID is returned
def test_getVerkey_success(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    ver_key = token_authnr.getVerkey(VALID_IDENTIFIER)
    assert len(ver_key) == 23
    assert ver_key[0] == '~'


# this tests that if the identifier is a payment address with a checksum, then a payment verkey is returned
def test_getVerkey_pay_address_success(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    # TODO change these to indicate they are addresses
    identifier_43 = 'sjw1ceG7wtym3VcnyaYtf1xo37gCUQHDR5VWcKWNPLRZ1X8eC'
    ver_key = token_authnr.getVerkey(identifier_43)
    assert ver_key == '8kjqqnF3m6agp9auU7k4TWAhuGygFAgPzbNH3shp4HFL'


# this tests that an exception is returned if an Unknown identifier is submitted
def test_getVerkey_invalid_identifier(node):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    identifier_invalid = 'INVALID_IDENTIFIER'
    with pytest.raises(UnknownIdentifier):
        token_authnr.getVerkey(identifier_invalid)


# -------------------------Test get_xfer_ser_data method----------------------------------------------------------------
@pytest.mark.skip
# This test verifies that given a properly formatted request will return xfer ser data
def test__get_xfer_ser_data_success(node, user2_token_wallet, user2_address,
                                    SF_token_wallet, SF_address, user1_address):
    token_authnr = TokenAuthNr(node[0].states[DOMAIN_LEDGER_ID])
    inputs = [[user2_token_wallet, user2_address, 1], [SF_token_wallet, SF_address, 2]]
    outputs = [[user1_address, 10], [user1_address, 10]]
    request = xfer_request(inputs, outputs)
    msg = request.as_dict
    ser_data = token_authnr._get_xfer_ser_data(msg, VALID_IDENTIFIER)
    assert ser_data[OPERATION][INPUTS] == []
    assert ser_data[OPERATION][OUTPUTS] == msg[OPERATION][OUTPUTS]
    assert ser_data[OPERATION][EXTRA] == msg[OPERATION][EXTRA]
    assert ser_data[f.REQ_ID.nm] == msg[f.REQ_ID.nm]
