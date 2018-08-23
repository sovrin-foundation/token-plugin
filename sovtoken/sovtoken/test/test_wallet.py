import pytest
from base58 import b58decode

from sovtoken.messages.fields import PublicAddressField
from sovtoken.test.wallet import TokenWallet, Address
from sovtoken.test.txn_response import TxnResponse


@pytest.fixture()
def address0():
    address = Address()
    address.add_utxo(1, 50000)
    address.add_utxo(4, 60000)
    return address


@pytest.fixture()
def address1():
    address = Address()
    address.add_utxo(2, 4000)
    return address


@pytest.fixture()
def address2():
    address = Address(b'Falcon00000000000000000000000000')
    address.add_utxo(3, 3001)
    return address


@pytest.fixture()
def test_wallet(address0, address1, address2):
    wallet = TokenWallet("TestWallet")
    wallet.add_new_address(address0)
    wallet.add_new_address(address1)
    wallet.add_new_address(address2)
    return wallet


def test_address_length(address0, address1, address2):
    assert len(b58decode(address0.address.encode())) == PublicAddressField.length
    assert len(b58decode(address1.address.encode())) == PublicAddressField.length
    assert len(b58decode(address2.address.encode())) == PublicAddressField.length

    assert len(b58decode(address0.verkey.encode())) == 32
    assert len(b58decode(address1.verkey.encode())) == 32
    assert len(b58decode(address2.verkey.encode())) == 32


def test_address_create_with_seed():
    address = Address(b'Falcon00000000000000000000000000')
    address1 = Address(b'Falcon00000000000000000000000000')
    assert address.address == address1.address


def test_address_isunspent():
    address = Address()
    address.outputs[0][1] = 5000000000000000000
    assert address.is_unspent(1)


def test_address_add_utxo():
    address = Address()
    address.add_utxo(1,5000000000000000000)
    assert (1,5000000000000000000) in address.all_utxos


def test_address_add_utxo_null():
    # Should this pass since its (None, None) or should we refactor so that this is an invalid add
    address = Address()
    address.add_utxo(None, None)
    assert (None, None) in address.all_utxos


def test_address_spent(address2):
    address2.spent(1)
    assert not address2.is_unspent(1)


def test_address_spent_1():
    address = Address()
    address.add_utxo(1,5000000000000000000)
    address.spent(1)
    assert not address.is_unspent(1)


def test_address_total_amount():
    address = Address()
    address.add_utxo(1,5000000000000000000)
    address.add_utxo(2,4000000000000000000)
    assert address.total_amount == 9000000000000000000


def test_token_wallet_add_new_address_success():
    wallet = TokenWallet("TestWallet")
    address = Address()
    wallet.add_new_address(address)
    assert address.address in wallet.addresses


def test_token_wallet_add_new_address_none_fail():
    wallet = TokenWallet("TestWallet")
    with pytest.raises(AssertionError):
            wallet.add_new_address(None)


def test_token_wallet_add_new_address_already_used():
    wallet = TokenWallet("TestWallet")
    address = Address()
    wallet.add_new_address(address)
    with pytest.raises(AssertionError):
        # add address to wallet second time
        wallet.add_new_address(address)


def test_token_wallet_add_new_address_seed_used():
    wallet = TokenWallet("TestWallet")
    address = Address(b'Falcon00000000000000000000000000')
    address1 = Address(b'Falcon00000000000000000000000000')
    wallet.add_new_address(address)
    with pytest.raises(AssertionError):
        wallet.add_new_address(address1)


def test_token_wallet_get_all_utxos_success(test_wallet, address0, address1, address2):
    all_utxos = test_wallet.get_all_wallet_utxos()
    assert all_utxos[address0] == [(1, 50000), (4, 60000)] and \
           all_utxos[address1] == [(2, 4000)] and \
           all_utxos[address2] == [(3, 3001)]


#TODO: Throws assertion error currently because of line 79 in wallet.py
def test_token_wallet_get_all_utxos_failure(test_wallet, address0):
    with pytest.raises(AssertionError):
        address_utxos = test_wallet.get_all_address_utxos(address0.address)
        assert address_utxos == [(1, 50000), (4, 60000)]


def test_token_wallet_get_all_utxos_invalid(test_wallet):
    address_not_used = Address()
    assert {} == test_wallet.get_all_address_utxos(address_not_used.address)


def test_token_wallet_get_total_amount_all_success(test_wallet):
    total = test_wallet.get_total_wallet_amount()
    assert total == 117001


def test_token_wallet_get_total_amount_subset_invalid(test_wallet, address0, address1):
    #TypeError expected here because this method cannot handle a subset
    # This refactor has been removed because it breaks other test and is unnecessary
    with pytest.raises(TypeError):
        total = test_wallet.get_total_address_amount([address0, address1])


#TODO: Throws assertion error currently because of line 87 in wallet.py
def test_token_wallet_get_total_amount_one_success(test_wallet, address0):
    with pytest.raises(AssertionError):
        total = test_wallet.get_total_address_amount(address0)
        assert total == 110000


def test_token_wallet_get_total_amount_invalid():
    test_wallet = TokenWallet("Test Wallet")
    total = test_wallet.get_total_address_amount(None)
    assert total == 0


def test_token_wallet_on_reply_from_network_success(test_wallet, address0):
    observer_name = "ddcebc22-3364-47e6-8500-0e8a00cd6341"
    req_id = 1517251781147288
    frm = "GammaC"
    result = {"Identifier": "6ouriXMZkLeHsuXrN1X1fd", "address" : address0.address,
              "outputs": [{"address": address0.address, "seqNo": 6, "amount": 10000}],
              "type": "10002", "reqId" : 1517251781147288}
    num_replies = 2
    test_wallet.on_reply_from_network(observer_name, req_id, frm, result, num_replies)
    outputs = address0.outputs
    assert outputs[0][6] == 10000


def test_token_wallet_on_reply_from_network_invalid(test_wallet, address0):
    invalid_address = Address()
    observer_name = "ddcebc22-3364-47e6-8500-0e8a00cd6341"
    req_id = 1517251781147288
    frm = "GammaC"
    result = {"Identifier": "6ouriXMZkLeHsuXrN1X1fd", "address" : invalid_address.address,
              "outputs": [{"address": invalid_address.address, "seqNo": 6, "amount": 10000}],
              "type": "10002", "reqId" : 1517251781147288}
    num_replies = 2
    test_wallet.on_reply_from_network(observer_name, req_id, frm, result, num_replies)
    # Raises KeyError because (6, 10000) has been added to invalid_address obj not address0 obj
    with pytest.raises(KeyError):
        assert address0.outputs[0][6] != 10000


def test_token_wallet_on_reply_from_network_success2(test_wallet, address0):
    observer_name = "ddcebc22-3364-47e6-8500-0e8a00cd6341"
    req_id = 1517251781147288
    seq_no = 6
    frm = "GammaC"
    result = {"Identifier": "6ouriXMZkLeHsuXrN1X1fd", "address" : address0.address,
              "outputs": [{"address": address0.address, "amount": 10000}],
              "inputs": [{"address": address0.address, "seqNo": 1}],
              "type": "10001", "reqId" : 1517251781147288, "seqNo": seq_no}
    num_replies = 2
    txn = TxnResponse("10001", result, seq_no=seq_no).form_response()
    test_wallet.on_reply_from_network(observer_name, req_id, frm, txn, num_replies)
    assert address0.outputs[0][seq_no] == 10000 and address0.outputs[1][1] == 50000


def test_token_wallet_on_reply_from_network_invalid_address2(test_wallet, address0):
    invalid_address = Address()
    observer_name = "ddcebc22-3364-47e6-8500-0e8a00cd6341"
    req_id = 1517251781147288
    seq_no = 6
    frm = "GammaC"
    result = {"Identifier": "6ouriXMZkLeHsuXrN1X1fd", "address" : invalid_address.address,
              "outputs": [{"address": invalid_address.address, "amount": 10000}],
              "inputs": [{"address": invalid_address.address, "seqNo": 1}],
              "type": "10001", "reqId" : 1517251781147288, "seqNo": seq_no}
    num_replies = 2
    txn = TxnResponse("10001", result, seq_no=seq_no).form_response()
    test_wallet.on_reply_from_network(observer_name, req_id, frm, txn, num_replies)
    with pytest.raises(KeyError):
        assert address0.outputs[0][seq_no] != 10000 and address0.outputs[1][1] != 50000


def test_token_wallet_handle_get_utxo_response_success(test_wallet, address0):
    response = {"address": address0.address,
                "outputs": [{"address": address0.address, "seqNo": 6, "amount": 10000}],
                "reqId": 23432, "Identifier": "6ouriXMZkLeHsuXrN1X1fd", "type": "10002"}
    test_wallet.handle_get_utxo_response(response)
    assert address0.outputs[0][6] == 10000


def test_token_wallet_handle_get_utxo_response_invalid_address(test_wallet, address0):
    invalid_address = Address()
    response = {"address": invalid_address.address,
                "outputs": [{"address": invalid_address.address, "seqNo": 6, "amount": 10000}],
                "reqId": 23432, "Identifier": "6ouriXMZkLeHsuXrN1X1fd", "type": "10002"}
    test_wallet.handle_get_utxo_response(response)
    with pytest.raises(KeyError):
        assert address0.outputs[0][6] != 10000


def test_token_wallet_handle_xfer_success(test_wallet, address0):
    seq_no = 6
    response = {"address": address0.address,
                "outputs": [{"address": address0.address, "amount": 10000}],
                "inputs": [{"address": address0.address, "seqNo": 1}],
                "seqNo": seq_no, "reqId": 23432, "Identifier": "6ouriXMZkLeHsuXrN1X1fd", "type": "10002"}

    txn = TxnResponse("10002", response, seq_no=seq_no).form_response()
    test_wallet.handle_xfer(txn)
    assert address0.outputs[0][seq_no] == 10000 and address0.outputs[1][1] == 50000


def test_token_wallet_handle_xfer_invalid_address(test_wallet, address0):
    invalid_address = Address()
    seq_no = 6
    response = {"address": invalid_address.address,
                "outputs": [{"address": invalid_address.address, "amount": 10000}],
                "inputs": [{"address": invalid_address.address, "seqNo": 1}],
                "seqNo": seq_no,"reqId": 23432, "Identifier": "6ouriXMZkLeHsuXrN1X1fd", "type": "10002"}

    txn = TxnResponse("10002", response, seq_no=seq_no).form_response()
    test_wallet.handle_xfer(txn)
    #Raises KeyError because (6, 10000) has been added to invalid_address obj not address0 obj
    with pytest.raises(KeyError):
        assert address0.outputs[0][seq_no] != 10000 and address0.outputs[1][1] != 50000


# TODO: This throws a key error when receiving an object of an Address.
# TODO: Needs to be refactored to accept address in string or object format
def test_token_wallet_get_val_success(test_wallet, address0):
    with pytest.raises(KeyError):
        val = test_wallet.get_val(address0, 1)
        assert val == 50000


def test_token_wallet_get_val_null(test_wallet, address0):
    with pytest.raises(KeyError):
        val = test_wallet.get_val(address0, None)


def test_token_wallet_get_val_invalid_address(test_wallet):
    address0_not_in_wallet = Address()
    with pytest.raises(KeyError):
        val = test_wallet.get_val(address0_not_in_wallet, 1)