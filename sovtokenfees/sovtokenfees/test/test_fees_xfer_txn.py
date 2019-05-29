import pytest

from plenum.common.exceptions import RequestRejectedException
from plenum.common.txn_util import get_seq_no, get_payload_data
from sovtoken.constants import ADDRESS, AMOUNT, SEQNO, PAYMENT_ADDRESS
from sovtokenfees.test.constants import XFER_PUBLIC_FEES_ALIAS


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture
def addresses_inner(helpers):
    return helpers.inner.wallet.create_new_addresses(2)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def send_transfer_request(helpers, mint_result, fees, addresses, adjust_fees=0):
    helpers.general.do_set_fees(fees)

    [address_giver, address_receiver] = addresses
    fee_amount = fees[XFER_PUBLIC_FEES_ALIAS] + adjust_fees

    inputs = helpers.general.get_utxo_addresses([address_giver])[0]
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
    fee_amount = fees[XFER_PUBLIC_FEES_ALIAS]

    [
        address_giver_utxos,
        address_receiver_utxos,
    ] = helpers.general.get_utxo_addresses(addresses)

    assert address_giver_utxos[0][PAYMENT_ADDRESS] == address_giver
    assert address_giver_utxos[0][AMOUNT] == 900 - fee_amount
    assert address_receiver_utxos[0][PAYMENT_ADDRESS] == address_receiver
    assert address_receiver_utxos[0][AMOUNT] == 100


def test_xfer_fees_with_empty_output(helpers, address_main_inner, fees):
    """
    Pay fees without transferring tokens in a transfer request.
    """
    address_giver = address_main_inner
    outputs = [{ADDRESS: "pay:sov:" + address_giver, AMOUNT: int(fees[XFER_PUBLIC_FEES_ALIAS])}]

    result = helpers.general.do_mint(outputs)
    seq_no = get_seq_no(result)

    helpers.general.do_set_fees(fees)

    inputs = [{ADDRESS: address_giver, SEQNO: seq_no}]
    outputs = []

    helpers.inner.general.do_transfer(inputs, outputs)


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

    inputs = helpers.general.get_utxo_addresses([address_giver])[0]
    outputs = [{ADDRESS: address_receiver, AMOUNT: 1000}]

    with pytest.raises(RequestRejectedException):
        helpers.general.do_transfer(inputs, outputs)

    utxos = helpers.general.get_utxo_addresses([address_giver])[0]

    assert utxos[0][PAYMENT_ADDRESS] == address_giver
    assert utxos[0][AMOUNT] == 1000


def test_xfer_with_additional_fees_attached(
    helpers,
    address_main_inner,
    mint_tokens_inner,
    fees
):
    """ Transfer request with fees and with fees attached on the fees field. """
    helpers.general.do_set_fees(fees)
    address_giver = address_main_inner
    address_receiver = helpers.inner.wallet.create_address()
    seq_no = get_seq_no(mint_tokens_inner)

    utxos = [{ADDRESS: address_giver, AMOUNT: 1000, SEQNO: seq_no}]
    inputs = helpers.inner.general.get_utxo_addresses([address_giver])[0]
    outputs = [{ADDRESS: address_receiver, AMOUNT: 1000 - fees[XFER_PUBLIC_FEES_ALIAS]}]

    request = helpers.inner.request.transfer(inputs, outputs)
    request = helpers.inner.request.add_fees(
        request,
        utxos,
        fees[XFER_PUBLIC_FEES_ALIAS],
        change_address=address_giver
    )

    result = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(result)


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

    utxos = helpers.general.get_utxo_addresses([address_giver])[0]

    assert utxos[0][PAYMENT_ADDRESS] == address_giver
    assert utxos[1][PAYMENT_ADDRESS] == address_giver
    assert utxos[0][AMOUNT] == 900 - fees[XFER_PUBLIC_FEES_ALIAS]
    assert utxos[1][AMOUNT] == 1000
