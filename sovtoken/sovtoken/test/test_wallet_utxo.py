import pytest
from sovtoken.test.wallet import TokenWallet, Address
from sovtoken.constants import OUTPUTS


@pytest.fixture
def addresses(helpers, wallet):
    addresses = helpers.wallet.add_new_addresses(wallet, 3)
    return [address.address for address in addresses]


@pytest.fixture
def wallet():
    return TokenWallet()


@pytest.fixture
def vals1(addresses):
    return [
        {"address": addresses[0], "amount": 1},
        {"address": addresses[1], "amount": 2},
        {"address": addresses[2], "amount": 10}
    ]


def test_wallet_update_outputs_with_invalid_output_format(wallet, addresses):
    with pytest.raises(ValueError):
        wallet._update_outputs([addresses[0]])


def test_wallet_update_outputs_with_no_txn_seq_no(wallet, vals1):
    with pytest.raises(ValueError):
        wallet._update_outputs(outputs=vals1)


def test_wallet_update_outputs_with_invalid_txn_seq_no_format(wallet, vals1):
    with pytest.raises(ValueError):
        wallet._update_outputs(outputs=vals1, txn_seq_no='3001')


def test_wallet_get_total_address_amount_same_txn_seq_no(
    wallet,
    addresses,
    vals1
):
    wallet._update_outputs(outputs=vals1, txn_seq_no=3001)
    assert wallet.get_total_address_amount(addresses[0]) == 1
    assert wallet.get_total_address_amount(addresses[1]) == 2
    assert wallet.get_total_address_amount(addresses[2]) == 10
    assert wallet.get_total_wallet_amount() == 13


def test_wallet_get_total_address_amount_diff_txn_seq_no(wallet, addresses):
    [address1, address2, address3] = addresses
    vals = [
        {"address": address1, "seqNo": 3002, "amount": 2},
        {"address": address2, "seqNo": 3002, "amount": 15},
        {"address": address2, "seqNo": 3003, "amount": 15},
        {"address": address2, "seqNo": 3004, "amount": 15},
        {"address": address3, "seqNo": 3003, "amount": 19}
    ]

    wallet._update_outputs(outputs=vals)

    assert wallet.get_total_address_amount(address1) == 2
    assert wallet.get_total_address_amount(address2) == 45
    assert wallet.get_total_address_amount(address3) == 19
    assert wallet.get_total_wallet_amount() == 66


def test_get_min_utxo_ge(wallet, addresses):
    [address1, address2, _] = addresses

    wallet._update_outputs(outputs=[{"address": address1, "seqNo": 3001, "amount": 1}])
    wallet._update_outputs(outputs=[
        {"address": address2, "seqNo": 3004, "amount": 3},
        {"address": address2, "seqNo": 9010, "amount": 4},
        {"address": address2, "seqNo": 3005, "amount": 15},
        {"address": address2, "seqNo": 1010, "amount": 16},
    ])

    assert wallet.get_min_utxo_ge(1) == {"address": address1, "seqNo": 3001, "amount": 1}
    assert wallet.get_min_utxo_ge(0, address=address1) == {"address": address1, "seqNo": 3001, "amount": 1}
    assert wallet.get_min_utxo_ge(1, address=address1) == {"address": address1, "seqNo": 3001, "amount": 1}
    assert wallet.get_min_utxo_ge(1, address=address2) == {"address": address2, "seqNo": 3004, "amount": 3}
    assert wallet.get_min_utxo_ge(3, address=address2) == {"address": address2, "seqNo": 3004, "amount": 3}
    assert wallet.get_min_utxo_ge(4, address=address2) == {"address": address2, "seqNo": 9010, "amount": 4}
    assert wallet.get_min_utxo_ge(11, address=address2) == {"address": address2, "seqNo": 3005, "amount": 15}
    assert wallet.get_min_utxo_ge(16, address=address2) == {"address": address2, "seqNo": 1010, "amount": 16}
    assert not wallet.get_min_utxo_ge(20, address=address2)


def test_update_multiple_address_outputs():
    wallet = TokenWallet()
    address1 = Address()
    address2 = Address()
    address3 = Address()
    wallet.add_new_address(address1)
    wallet.add_new_address(address2)
    fake_get_utxo_resp = {
        OUTPUTS: [
            {"address": address1.address, "seqNo": 1, "amount": 10},
            {"address": address1.address, "seqNo": 2, "amount": 10},
            {"address": address2.address, "seqNo": 3, "amount": 10},
            {"address": address3.address, "seqNo": 4, "amount": 30}
        ]
    }
    wallet.handle_get_utxo_response(fake_get_utxo_resp)
    assert 20 == wallet.get_total_address_amount(address1.address)
    assert 10 == wallet.get_total_address_amount(address2.address)
    assert 0 == wallet.get_total_address_amount(address3.address)
