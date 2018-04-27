from plenum.common.constants import NYM
from plenum.server.plugin.fees.src.constants import FEES
from plenum.server.plugin.fees.src.wallet import FeeSupportedWallet
from plenum.server.plugin.token.src.wallet import Address
from plenum.server.plugin.fees.test.demo_helper import methods

MINT_TOKEN_AMOUNT = 10

TXN_FEES = {
    NYM: 3
}


def test_demo_fees_on_nym_transaction(methods):
    client_wallet = FeeSupportedWallet("RichDemoWallet")
    client_address = Address()
    client_wallet.add_new_address(client_address)

    set_reply = methods.set_fees(TXN_FEES)
    assert set_reply['result'][FEES][NYM] == TXN_FEES[NYM]

    fees = methods.get_fees()
    assert fees[NYM] == TXN_FEES[NYM]

    mint_tokens_reply = methods.mint_tokens(client_address.address, MINT_TOKEN_AMOUNT)
    [reply_address, reply_tokens] = mint_tokens_reply['result']['outputs'][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT

    assert methods.get_utxo_at_wallet_address(client_wallet, client_address) == [(1, 10)]

    nym_request = methods.create_nym_request(client_wallet, client_address)
    nym_reply = methods.send_nym_request(nym_request)
    [reply_address, reply_tokens] = nym_reply['result'][FEES][1][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT - TXN_FEES[NYM]


    # Steps 6 and 7 are not complete
    # Step 6 - tokens are removed from wallet on fees:
    # assert methods.get_utxo_at_wallet_address(client_wallet, client_address) == [(2, MINT_TOKEN_AMOUNT - TXN_FEES[NYM])]
    #
    # Step 7 - tokens are in SF address


