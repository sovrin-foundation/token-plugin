import pytest

from plenum.common.exceptions import RequestRejectedException
from plenum.common.txn_util import get_seq_no, get_payload_data
from sovtoken.constants import XFER_PUBLIC, OUTPUTS, ADDRESS, AMOUNT, SEQNO


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def send_transfer_request(helpers, mint_result, fees, addresses, adjust_fees=0):
    helpers.general.do_set_fees(fees)

    [address_giver, address_receiver] = addresses
    mint_seq_no = get_seq_no(mint_result)
    fee_amount = fees[XFER_PUBLIC] + adjust_fees

    inputs = [{ADDRESS: address_giver, SEQNO: mint_seq_no}]
    outputs = [
        {ADDRESS: address_receiver, AMOUNT: 100},
        {ADDRESS: address_giver, AMOUNT: 900 - fee_amount},
    ]
    result = helpers.general.do_transfer(inputs, outputs)

    return result


# Attempt a transfer transaction with insufficient fees.
def test_xfer_with_insufficient_fees(
    helpers,
    addresses,
    mint_tokens,
    fees,
):
    with pytest.raises(RequestRejectedException):
        send_transfer_request(
            helpers,
            mint_tokens,
            fees,
            addresses,
            adjust_fees=-1
        )


# Attempt a transfer transaction with extra fees.
def test_xfer_with_extra_fees(
    helpers,
    addresses,
    mint_tokens,
    fees,
):
    with pytest.raises(RequestRejectedException):
        send_transfer_request(
            helpers,
            mint_tokens,
            fees,
            addresses,
            adjust_fees=1
        )


def test_xfer_with_sufficient_fees(
    helpers,
    addresses,
    mint_tokens,
    fees,
):
    [address_giver, address_receiver] = addresses
    result = send_transfer_request(helpers, mint_tokens, fees, addresses)
    transfer_seq_no = get_seq_no(result)
    fee_amount = fees[XFER_PUBLIC]

    [
        address_giver_utxos,
        address_receiver_utxos,
    ] = helpers.general.get_utxo_addresses(addresses)

    assert address_giver_utxos == [{
        ADDRESS: address_giver,
        SEQNO: transfer_seq_no,
        AMOUNT: 900 - fee_amount
    }]
    assert address_receiver_utxos == [{
        ADDRESS: address_receiver,
        SEQNO: transfer_seq_no,
        AMOUNT: 100
    }]

    helpers.node.assert_deducted_fees(XFER_PUBLIC, transfer_seq_no, fee_amount)


def test_invalid_xfer_with_valid_fees(
    helpers,
    addresses,
    mint_tokens,
    fees
):
    """
    Fees aren't paid when the payment address doesn't contain enough tokens for
    the transfer.
    """
    helpers.general.do_set_fees(fees)
    [address_giver, address_receiver] = addresses
    seq_no = get_seq_no(mint_tokens)

    inputs = [{ADDRESS: address_giver, SEQNO: seq_no}]
    outputs = [{ADDRESS: address_receiver, AMOUNT: 1000}]

    with pytest.raises(RequestRejectedException):
        helpers.general.do_transfer(inputs, outputs)

    utxos = helpers.general.get_utxo_addresses([address_giver])

    assert utxos == [[
        {ADDRESS: address_giver, AMOUNT: 1000, SEQNO: seq_no}
    ]]


def test_xfer_with_additional_fees_attached(
    helpers,
    addresses,
    mint_tokens,
    fees
):
    """ Transfer request with fees and with fees attached on the fees field. """

    helpers.general.do_set_fees(fees)
    [address_giver, address_receiver] = addresses
    seq_no = get_seq_no(mint_tokens)

    utxos = [{ADDRESS: address_giver, AMOUNT: 1000, SEQNO: seq_no}]
    inputs = [{ADDRESS: address_giver, SEQNO: seq_no}]
    outputs = [{ADDRESS: address_receiver, AMOUNT: 1000 - fees[XFER_PUBLIC]}]

    request = helpers.request.transfer(inputs, outputs)
    request = helpers.request.add_fees(
        request,
        utxos,
        fees[XFER_PUBLIC],
        change_address=address_giver
    )

    result = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(result)

    xfer_seq_no = get_seq_no(result)
    key = "{}#{}".format(XFER_PUBLIC, xfer_seq_no)
    fees_req_handler = helpers.node.get_fees_req_handler()

    assert fees[XFER_PUBLIC] == fees_req_handler.deducted_fees[key]
    assert key not in fees_req_handler.deducted_fees_xfer


# Mint after a transfer transaction with fees
def test_mint_after_paying_fees(
    helpers,
    addresses,
    mint_tokens,
    fees
):
    xfer_result = send_transfer_request(helpers, mint_tokens, fees, addresses)

    address_giver = addresses[0]
    outputs = [{ADDRESS: address_giver, AMOUNT: 1000}]
    mint_result = helpers.general.do_mint(outputs)
    xfer_seq_no = get_seq_no(xfer_result)
    mint_seq_no = get_seq_no(mint_result)

    utxos = helpers.general.do_get_utxo(address_giver)[OUTPUTS]

    assert utxos == [
        {
            ADDRESS: address_giver,
            SEQNO: xfer_seq_no,
            AMOUNT: 900 - fees[XFER_PUBLIC]
        },
        {
            ADDRESS: address_giver,
            SEQNO: mint_seq_no,
            AMOUNT: 1000
        }
    ]
