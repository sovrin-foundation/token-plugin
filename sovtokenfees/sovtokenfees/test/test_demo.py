import pytest
from plenum.common.constants import NYM
from plenum.common.txn_util import get_payload_data, get_seq_no
from sovtokenfees.constants import FEES
from sovtoken.constants import OUTPUTS, TOKEN_LEDGER_ID
from sovtoken.test.demo.demo_helpers import demo_logger


MINT_TOKEN_AMOUNT = 100

TXN_FEES = {
    NYM: 5
}


step1_info = """
    Create an address
"""
def create_client_address(helpers):
    client_address = helpers.wallet.create_address()

    demo_logger.log_header(step1_info)
    demo_logger.log_blue("Client address is {}".format(client_address.address))

    return client_address


step2_info = """
    Set a fee for nym transactions.
"""
def set_fee_for_nym_transactions(helpers):
    result = helpers.general.do_set_fees(TXN_FEES)
    assert get_payload_data(result)[FEES][NYM] == TXN_FEES[NYM]

    demo_logger.log_header(step2_info)
    demo_logger.log_blue("Set sovtokenfees equal to:")
    demo_logger.log_yellow(TXN_FEES)
    demo_logger.log_blue("{} is the identifier for a NYM request".format(NYM))


step3_info = """
    Get current fees and assert the fee is set for nym transactions.
"""
def check_fee_set_for_nym_transactions(helpers):
    fees = helpers.general.do_get_fees()[FEES]
    assert fees[NYM] == TXN_FEES[NYM]

    demo_logger.log_header(step3_info)
    demo_logger.log_blue("Ledger's fees equaled:")
    demo_logger.log_yellow(TXN_FEES)


step4_info = """
    Mint tokens for the client.
"""
def mint_tokens_to_client(helpers, client_address):
    result = helpers.general.do_mint([[client_address, MINT_TOKEN_AMOUNT]])
    [reply_address, reply_tokens] = get_payload_data(result)[OUTPUTS][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT
    client_utxos = helpers.general.get_utxo_addresses([client_address])[0]
    assert client_utxos == [[client_address, 1, MINT_TOKEN_AMOUNT]]

    formatted_utxos = [(utxo[0].address, utxo[1], utxo[2]) for utxo in client_utxos]
    demo_logger.log_header(step4_info)
    demo_logger.log_blue("Minted {} tokens to Client".format(MINT_TOKEN_AMOUNT))
    demo_logger.log_blue("Client address {} contained utxo:".format(client_address.address))
    demo_logger.log_yellow(formatted_utxos[0])
    demo_logger.log_blue("utxo format is (address, sequence_number, tokens)")

    return client_utxos


step5_info = """
    Send a nym request.
"""
def create_and_send_nym_request(helpers, client_address, client_utxos):
    # =============
    # Create nym request and add fees.
    # =============

    nym_request = helpers.request.nym()
    nym_request = helpers.request.add_fees(
        nym_request,
        client_utxos,
        fee_amount=TXN_FEES[NYM],
        change_address=client_address,
    )

    # =============
    # Send nym request.
    # =============

    responses = helpers.sdk.send_and_check_request_objects([nym_request])
    result = helpers.sdk.get_first_result(responses)

    formatted_request = demo_logger.format_json(nym_request.as_dict)
    demo_logger.log_header(step5_info)
    demo_logger.log_blue("Sent NYM request:")
    demo_logger.log_yellow(formatted_request)

    return result


step6_info = """
    Tokens charged for fee are no longer in the client wallet.
"""
def check_tokens_at_address(helpers, client_address):
    client_utxos = helpers.general.get_utxo_addresses([client_address])[0]
    expected_amount = MINT_TOKEN_AMOUNT - TXN_FEES[NYM]
    assert client_utxos == [[client_address, 2, expected_amount]]

    formatted_utxos = [(utxo[0].address, utxo[1], utxo[2]) for utxo in client_utxos]
    demo_logger.log_header(step6_info)
    demo_logger.log_blue("Client address {} contained utxo:".format(client_address.address))
    demo_logger.log_yellow(formatted_utxos[0])
    demo_logger.log_blue("utxo format is (address, sequence_number, tokens)")


step7_info = """
    Fee transaction is on the ledger.
"""
def check_fee_request_on_ledger(helpers, client_address, nym_result):
    transactions = helpers.node.get_last_ledger_transaction_on_nodes(TOKEN_LEDGER_ID)
    for fee_txn in transactions:
        fee_data = get_payload_data(fee_txn)
        assert fee_data[OUTPUTS] == [[client_address.address, MINT_TOKEN_AMOUNT - TXN_FEES[NYM]]]
        assert fee_data[FEES] == TXN_FEES[NYM]
        assert get_seq_no(fee_txn) == 2

    nym_seq_no = get_seq_no(nym_result)
    helpers.node.assert_deducted_fees(NYM, nym_seq_no, TXN_FEES[NYM])

    formatted_txn = demo_logger.format_json(transactions[0])
    demo_logger.log_header(step7_info)
    demo_logger.log_blue("Fee transaction found on Payment ledger:")
    demo_logger.log_yellow(formatted_txn)


# TODO Fees are distributed
step8_info = """
    Fees are automatically distributed.
"""
def distribute_fees():
    demo_logger.log_header(step8_info)
    demo_logger.log_blue("Not implemented")


def test_demo_fees_on_nym_transaction(helpers):
    demo_logger.log_header("Started Fees Test")

    client_address = create_client_address(helpers)

    set_fee_for_nym_transactions(helpers)

    check_fee_set_for_nym_transactions(helpers)

    utxos = mint_tokens_to_client(helpers, client_address)

    nym_result = create_and_send_nym_request(helpers, client_address, utxos)

    check_tokens_at_address(helpers, client_address)

    check_fee_request_on_ledger(helpers, client_address, nym_result)

    distribute_fees()

    demo_logger.log_header("Ended Fees Test")
