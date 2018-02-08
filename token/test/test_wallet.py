import pytest
from plenum.server.plugin.token.wallet import TokenWallet, Address

def test_address_isunspent():
    address = Address()
    address.outputs[0][1] = 5000000000000000000
    assert address.is_unspent(1)

def test_address_add_utxo():
    address = Address()
    address.add_utxo(1,5000000000000000000)
    assert (1,5000000000000000000) in address.all_utxos

def test_address_spent():
    address = Address()
    address.add_utxo(1,5000000000000000000)
    address.spent(1)
    assert not address.is_unspent(1)

def test_address_total_amount():
    address = Address()
    address.add_utxo(1,5000000000000000000)
    address.add_utxo(2,4000000000000000000)
    assert address.total_amount == 9000000000000000000

def test_token_wallet_add_new_address():
    wallet = TokenWallet("TestWallet")
    address = Address()
    wallet.add_new_address(address)
    assert address.address in wallet.addresses