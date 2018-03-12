import pytest
from plugin.tokens.src.wallet import TokenWallet, Address


@pytest.fixture(scope="module")
def address1():
    return Address()


@pytest.fixture(scope="module")
def address2():
    return Address()


@pytest.fixture(scope="module")
def address3():
    return Address()


@pytest.fixture(scope="module")
def wallet(address1, address2, address3):
    wally = TokenWallet()
    wally.add_new_address(address1)
    wally.add_new_address(address2)
    wally.add_new_address(address3)
    return wally


@pytest.fixture(scope="module")
def vals1(address1, address2, address3):
    return [(address1.address, 1), (address2.address, 2), (address3.address, 10)]


def test_wallet_update_outputs_with_invalid_output_format(wallet, address1):
    with pytest.raises(ValueError):
        wallet._update_outputs([address1.address])


def test_wallet_update_outputs_with_no_txn_seq_no(wallet, vals1):
    with pytest.raises(ValueError):
        wallet._update_outputs(outputs=vals1)


def test_wallet_update_outputs_with_invalid_txn_seq_no_format(wallet, vals1):
    with pytest.raises(ValueError):
        wallet._update_outputs(outputs=vals1, txn_seq_no='3001')


def test_wallet_get_total_amount_with_outputs_with_same_txn_seq_no(wallet,
                                                                   address1,
                                                                   address2,
                                                                   address3,
                                                                   vals1):
    wallet._update_outputs(outputs=vals1, txn_seq_no=3001)
    assert wallet.get_total_address_amount(address1.address) == 1
    assert wallet.get_total_address_amount(address2.address) == 2
    assert wallet.get_total_address_amount(address3.address) == 10
    assert wallet.get_total_wallet_amount() == 13

#This test builds on the previous test
def test_wallet_get_total_amount_with_outputs_with_diff_txn_seq_no(wallet,
                                                                   address1,
                                                                   address2,
                                                                   address3):
    vals = [(address1.address, 3002, 1), (address2.address, 3002, 2),
            (address3.address, 3003, 10)]
    # This adds to the updated outputs from the previous test
    wallet._update_outputs(outputs=vals)
    #These results are valid because they are combined with the updated amounts
    #  in the previous test
    assert wallet.get_total_address_amount(address1.address) == 2
    assert wallet.get_total_address_amount(address2.address) == 4
    assert wallet.get_total_address_amount(address3.address) == 20
    assert wallet.get_total_wallet_amount() == 26

#This test builds on the previous test
def test_get_min_utxo_ge(wallet, address1, address2, address3):
    # These add to the updated outputs from the previous test
    wallet._update_outputs(outputs=[(address3.address, 3004, 3)])
    wallet._update_outputs(outputs=[(address3.address, 9010, 4)])
    wallet._update_outputs(outputs=[(address3.address, 3005, 15)])
    wallet._update_outputs(outputs=[(address3.address, 1010, 16)])
    # These results are valid because they find the updated amounts from the
    # previous test
    assert wallet.get_min_utxo_ge(0) == (address1.address, 3001, 1)
    assert wallet.get_min_utxo_ge(1) == (address1.address, 3001, 1)
    assert wallet.get_min_utxo_ge(1, address=address3.address) == \
           (address3.address, 3004, 3)
    assert wallet.get_min_utxo_ge(2, address=address3.address) == \
           (address3.address, 3004, 3)
    assert wallet.get_min_utxo_ge(3, address=address3.address) == \
           (address3.address, 3004, 3)
    assert wallet.get_min_utxo_ge(4, address=address3.address) == \
           (address3.address, 9010, 4)
    assert wallet.get_min_utxo_ge(5, address=address3.address) == \
           (address3.address, 3001, 10)
    assert wallet.get_min_utxo_ge(11, address=address3.address) == \
           (address3.address, 3005, 15)

def test_wallet_update_outputs_repeating_address_with_same_txn_seq_no(wallet,
                                                                      address1,
                                                                      address2,
                                                                      address3):
    vals = [(address1.address, 1), (address1.address, 2),
            (address3.address, 10)]
    with pytest.raises(AssertionError):
        wallet._update_outputs(outputs=vals, txn_seq_no=2)


