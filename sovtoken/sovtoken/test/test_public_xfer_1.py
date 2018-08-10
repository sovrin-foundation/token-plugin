import pytest

from plenum.common.txn_util import get_seq_no
from plenum.common.exceptions import RequestNackedException
from plenum.common.types import OPERATION
from sovtoken.constants import SIGS
from sovtoken.test.helper import user1_token_wallet


@pytest.fixture
def addresses(helpers, user1_token_wallet):
    return helpers.wallet.add_new_addresses(user1_token_wallet, 5)


@pytest.fixture
def initial_mint(helpers, addresses):
    outputs = [[address, 100] for address in addresses]
    mint_request = helpers.request.mint(outputs)
    responses = helpers.sdk.send_and_check_request_objects([mint_request])
    result = helpers.sdk.get_first_result(responses)
    return result


def test_multiple_inputs_with_1_incorrect_input_sig(  # noqa
    helpers,
    addresses,
    initial_mint,
):
    mint_seq_no = get_seq_no(initial_mint)
    [address1, address2, address3, *_] = addresses

    # Multiple inputs are used in a transaction but one of the inputs
    # has incorrect signature
    inputs = [[address1, mint_seq_no], [address2, mint_seq_no]]
    outputs = [[address3, 200]]

    request = helpers.request.transfer(inputs, outputs)
    operation = getattr(request, OPERATION)
    # Change signature for 2nd input, set it same as the 1st input's signature
    operation[SIGS][1] = operation[SIGS][0]
    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_multiple_inputs_with_1_missing_sig(  # noqa
    helpers,
    addresses,
    initial_mint,
):
    # Multiple inputs are used in a transaction but one of the inputs's
    # signature is missing, so there are 3 inputs but only 2 signatures.
    mint_seq_no = get_seq_no(initial_mint)
    [address1, address2, address3, *_] = addresses

    inputs = [[address1, mint_seq_no], [address2, mint_seq_no]]
    outputs = [[address3, 200]]

    # Remove signature for 2nd input
    request = helpers.request.transfer(inputs, outputs)
    request.operation[SIGS].pop()
    assert len(request.operation[SIGS]) == (len(inputs) - 1)

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_inputs_contain_signature_not_in_inputs(
    helpers,
    addresses,
    initial_mint
):
    # Add signature from an address not present in input

    mint_seq_no = get_seq_no(initial_mint)
    [address1, address2, address3, address4, *_] = addresses

    inputs = [[address1, mint_seq_no], [address2, mint_seq_no]]
    outputs = [[address3, 200]]

    request = helpers.request.transfer(inputs, outputs)

    extra_sig = helpers.wallet.payment_signatures(
        [[address4, mint_seq_no]],
        outputs
    )[0]

    request.operation[SIGS][1] = extra_sig

    assert len(request.operation[SIGS]) == len(inputs)
    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_multiple_inputs_outputs_without_change(
    helpers,
    addresses,
    initial_mint
):
    [address1, address2, address3, address4, address5] = addresses
    mint_seq_no = get_seq_no(initial_mint)

    inputs = [
        [address1, mint_seq_no],
        [address2, mint_seq_no],
        [address3, mint_seq_no],
    ]

    outputs = [
        [address4, 200],
        [address5, 100],
    ]

    request = helpers.request.transfer(inputs, outputs)
    response = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(response)
    xfer_seq_no = get_seq_no(result)

    [
        address1_utxos,
        address2_utxos,
        address3_utxos,
        address4_utxos,
        address5_utxos
    ] = helpers.general.get_utxo_addresses(addresses)

    assert address1_utxos == []
    assert address2_utxos == []
    assert address3_utxos == []
    assert address4_utxos == [
        [address4, mint_seq_no, 100],
        [address4, xfer_seq_no, 200],
    ]
    assert address5_utxos == [
        [address5, mint_seq_no, 100],
        [address5, xfer_seq_no, 100],
    ]


def test_multiple_inputs_outputs_with_change(
    helpers,
    addresses,
    initial_mint,
    user1_token_wallet,
):
    [address1, address2, address3, address4, address5] = addresses
    mint_seq_no = get_seq_no(initial_mint)

    inputs = [
        [address1, mint_seq_no],
        [address2, mint_seq_no],
        [address3, mint_seq_no],
    ]

    outputs = [
        [address4, 270],
        [address5, 10],
        [address1, 20]
    ]

    request = helpers.request.transfer(inputs, outputs)
    response = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(response)
    xfer_seq_no = get_seq_no(result)

    [
        address1_utxos,
        address2_utxos,
        address3_utxos,
        address4_utxos,
        address5_utxos
    ] = helpers.general.get_utxo_addresses(addresses)

    assert address1_utxos == [[address1, xfer_seq_no, 20]]
    assert address2_utxos == []
    assert address3_utxos == []
    assert address4_utxos == [
        [address4, mint_seq_no, 100],
        [address4, xfer_seq_no, 270],
    ]
    assert address5_utxos == [
        [address5, mint_seq_no, 100],
        [address5, xfer_seq_no, 10],
    ]
