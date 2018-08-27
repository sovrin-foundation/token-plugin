import pytest

from plenum.common.exceptions import RequestRejectedException
from plenum.common.txn_util import get_seq_no
from sovtoken.constants import XFER_PUBLIC, OUTPUTS


@pytest.fixture()
def addresses(helpers, user1_token_wallet):
    return helpers.wallet.add_new_addresses(user1_token_wallet, 2)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [[addresses[0], 1000]]
    return helpers.general.do_mint(outputs)


def send_transfer_request(helpers, mint_result, fees, addresses, adjust_fees=0):
    helpers.general.do_set_fees(fees)

    [address_giver, address_receiver] = addresses
    mint_seq_no = get_seq_no(mint_result)
    fee_amount = fees[XFER_PUBLIC] + adjust_fees

    inputs = [[address_giver, mint_seq_no]]
    outputs = [[address_receiver, 100], [address_giver, 900 - fee_amount]]
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

    assert address_giver_utxos == [
        [address_giver, transfer_seq_no, 900 - fee_amount]
    ]
    assert address_receiver_utxos == [
        [address_receiver, transfer_seq_no, 100]
    ]

    helpers.node.assert_deducted_fees(XFER_PUBLIC, transfer_seq_no, fee_amount)


# Mint after a transfer transaction with fees
def test_mint_after_paying_fees(
    helpers,
    addresses,
    mint_tokens,
    fees
):
    xfer_result = send_transfer_request(helpers, mint_tokens, fees, addresses)

    address_giver = addresses[0]
    outputs = [[address_giver, 1000]]
    mint_result = helpers.general.do_mint(outputs)
    xfer_seq_no = get_seq_no(xfer_result)
    mint_seq_no = get_seq_no(mint_result)

    utxos = helpers.general.do_get_utxo(address_giver)[OUTPUTS]

    assert utxos == [
        [address_giver.address, xfer_seq_no, 900 - fees[XFER_PUBLIC]],
        [address_giver.address, mint_seq_no, 1000],
    ]
