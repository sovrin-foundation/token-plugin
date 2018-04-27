from plenum.common.constants import NYM
from plenum.server.plugin.fees.src.constants import FEES
from plenum.server.plugin.fees.src.wallet import FeeSupportedWallet
from plenum.server.plugin.token.src.wallet import Address
from plenum.server.plugin.fees.test.demo_helper import methods


''' 
# class DemoMethods

This class wraps helpers (defined in places like helper.py) 
with our pytest fixtures.

The DemoMethods instance is passed into the test functions as the parameter "methods"

## Methods
    mint_tokens(address, tokens)

    set_fees(fees)

    get_fees()

    update_wallet(wallet)

    get_utxo_at_wallet_address(wallet, address)

    create_nym_request(wallet, fees_address)

    send_nym_request(nym_request)

'''

MINT_TOKEN_AMOUNT = 10

TXN_FEES = {
    NYM: 3
}


def create_client_wallet_and_address():
    client_wallet = FeeSupportedWallet("RichDemoWallet")
    client_address = Address()
    client_wallet.add_new_address(client_address)
    return (client_wallet, client_address)


def set_fee_for_nym_transactions(methods):
    set_reply = methods.set_fees(TXN_FEES)
    assert set_reply['result'][FEES][NYM] == TXN_FEES[NYM]


def check_fee_set_for_nym_transactions(methods):
    fees = methods.get_fees()
    assert fees[NYM] == TXN_FEES[NYM]


def mint_tokens_to_client(methods, client_wallet, client_address):
    mint_tokens_reply = methods.mint_tokens(client_address.address, MINT_TOKEN_AMOUNT)
    [reply_address, reply_tokens] = mint_tokens_reply['result']['outputs'][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT
    assert methods.get_utxo_at_wallet_address(client_wallet, client_address) == [(1, 10)]


def create_and_send_nym_request(methods, client_wallet, client_address):
    nym_request = methods.create_nym_request(client_wallet, client_address)
    nym_reply = methods.send_nym_request(nym_request)
    [reply_address, reply_tokens] = nym_reply['result'][FEES][1][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT - TXN_FEES[NYM]


def check_fee_tokens_removed_from_wallet(methods, client_wallet, client_address):
    # assert methods.get_utxo_at_wallet_address(client_wallet, client_address) == [(2, MINT_TOKEN_AMOUNT - TXN_FEES[NYM])]
    pass


def sovrin_foundation_collects_fees(methods):
    pass


def test_demo_fees_on_nym_transaction(methods):
    (client_wallet, client_address) = create_client_wallet_and_address()

    set_fee_for_nym_transactions(methods)

    check_fee_set_for_nym_transactions(methods)

    mint_tokens_to_client(methods, client_wallet, client_address)

    create_and_send_nym_request(methods, client_wallet, client_address)

    # Steps 6 and 7 are not complete
    # Step 6 - tokens are removed from wallet on fees:
    # Step 7 - tokens are in SF address

    check_fee_tokens_removed_from_wallet(methods, client_wallet, client_address)

    sovrin_foundation_collects_fees(methods)




