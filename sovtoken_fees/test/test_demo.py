from plenum.common.constants import NYM
from plenum.common.types import f
from plenum.server.plugin.sovtoken_fees.src.constants import FEES
from plenum.server.plugin.sovtoken_fees.src.wallet import FeeSupportedWallet
from plenum.server.plugin.sovtoken.src.constants import OUTPUTS, TOKEN_LEDGER_ID
from plenum.server.plugin.sovtoken.src.util import update_token_wallet_with_result
from plenum.server.plugin.sovtoken.src.wallet import Address
from plenum.server.plugin.sovtoken_fees.test.demo_helper import methods
from plenum.server.plugin.sovtoken.test.demo.demo_helpers import demo_logger


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
    
    get_last_ledger_transaction_on_all_nodes(ledger_id):

'''

MINT_TOKEN_AMOUNT = 100

TXN_FEES = {
    NYM: 5
}

step1_info = """
    Create a client wallet with an address in it.
"""
def create_client_wallet_and_address():
    client_wallet = FeeSupportedWallet("RichDemoWallet")
    client_address = Address()
    client_wallet.add_new_address(client_address)

    demo_logger.log_header(step1_info)
    demo_logger.log_blue("Created Client Wallet")
    demo_logger.log_blue("Client address is {}".format(client_address.address))

    return (client_wallet, client_address)


step2_info = """
    Set a fee for nym transactions.
"""
def set_fee_for_nym_transactions(methods):
    set_reply = methods.set_fees(TXN_FEES)
    assert set_reply['result'][FEES][NYM] == TXN_FEES[NYM]

    demo_logger.log_header(step2_info)
    demo_logger.log_blue("Set sovtoken_fees equal to:")
    demo_logger.log_yellow(TXN_FEES)
    demo_logger.log_blue("{} is the identifier for a NYM request".format(NYM))


step3_info = """
    Get current fees and assert the fee is set for nym transactions.
"""
def check_fee_set_for_nym_transactions(methods):
    fees = methods.get_fees()
    assert fees[NYM] == TXN_FEES[NYM]

    demo_logger.log_header(step3_info)
    demo_logger.log_blue("Ledger's fees equaled:")
    demo_logger.log_yellow(TXN_FEES)


step4_info = """
    Mint tokens for the client.
"""
def mint_tokens_to_client(methods, client_wallet, client_address):
    mint_tokens_reply = methods.mint_tokens(client_address.address, MINT_TOKEN_AMOUNT)
    [reply_address, reply_tokens] = mint_tokens_reply['result']['outputs'][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT
    utxo_at_client_wallet_address = methods.get_utxo_at_wallet_address(client_wallet, client_address)
    assert utxo_at_client_wallet_address == [(1, MINT_TOKEN_AMOUNT)]

    demo_logger.log_header(step4_info)
    demo_logger.log_blue("Minted {} tokens to Client".format(MINT_TOKEN_AMOUNT))
    demo_logger.log_blue("Client wallet contained utxo at address {}:".format(client_address.address))
    demo_logger.log_yellow(utxo_at_client_wallet_address)
    demo_logger.log_blue("utxo format is (sequence_number, tokens)")


step5_info = """
    Send a nym request.
"""
def create_and_send_nym_request(methods, client_wallet, client_address):
    nym_request = methods.create_nym_request(client_wallet, client_address)
    nym_result = methods.send_nym_request(nym_request)['result']
    [reply_address, reply_tokens] = nym_result[FEES][1][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT - TXN_FEES[NYM]
    update_token_wallet_with_result(client_wallet, nym_result)

    demo_logger.log_header(step5_info)
    demo_logger.log_blue("Sent NYM request:")
    demo_logger.log_yellow(nym_request)


step6_info = """
    Tokens charged for fee are no longer in the client wallet.
"""
def check_fee_tokens_removed_from_wallet(methods, client_wallet, client_address):
    utxo_at_client_wallet_address = methods.get_utxo_at_wallet_address(client_wallet, client_address)
    assert utxo_at_client_wallet_address == [(2, MINT_TOKEN_AMOUNT - TXN_FEES[NYM])]

    demo_logger.log_header(step6_info)
    demo_logger.log_blue("Client wallet contained utxo at address {}:".format(client_address.address))
    demo_logger.log_yellow(utxo_at_client_wallet_address)


step7_info = """
    Fee transaction is on the ledger.
"""
def check_fee_request_on_ledger(methods, client_address):
    transactions = methods.get_last_ledger_transaction_on_all_nodes(TOKEN_LEDGER_ID)
    for fees in transactions:
        assert fees[OUTPUTS] == [[client_address.address, MINT_TOKEN_AMOUNT - TXN_FEES[NYM]]]
        assert fees[FEES] == TXN_FEES[NYM]
        assert fees[f.SEQ_NO.nm] == 2

    demo_logger.log_header(step7_info)
    demo_logger.log_blue("Transaction found on Token ledger:")
    demo_logger.log_yellow(transactions[0])


# TODO Sovrin foundation collects sovtoken_fees
step8_info = """
    Sovrin foundation collects fees.
"""
def sovrin_foundation_collects_fees(methods):
    demo_logger.log_header(step8_info)
    demo_logger.log_blue("Not implemented")


def test_demo_fees_on_nym_transaction(methods):
    demo_logger.log_header("Started Fees Test")

    (client_wallet, client_address) = create_client_wallet_and_address()

    set_fee_for_nym_transactions(methods)

    check_fee_set_for_nym_transactions(methods)

    mint_tokens_to_client(methods, client_wallet, client_address)

    create_and_send_nym_request(methods, client_wallet, client_address)

    check_fee_tokens_removed_from_wallet(methods, client_wallet, client_address)

    check_fee_request_on_ledger(methods, client_address)

    sovrin_foundation_collects_fees(methods)

    demo_logger.log_header("Ended Fees Test")




