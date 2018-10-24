import pytest

from plenum.common.txn_util import get_seq_no
from plenum.common.exceptions import RequestNackedException
from plenum.common.types import OPERATION
from sovtoken.constants import SIGS, ADDRESS, SEQNO, AMOUNT, OUTPUTS
from sovtoken.test.helper import user1_token_wallet


@pytest.fixture
def addresses(helpers, user1_token_wallet):
    return helpers.wallet.add_new_addresses(user1_token_wallet, 5)


@pytest.fixture
def initial_mint(helpers, addresses):
    outputs = [{"address": address, "amount": 100} for address in addresses]
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
    inputs = [{"address": address1, "seqNo": mint_seq_no}, {"address": address2, "seqNo": mint_seq_no}]
    outputs = [{"address": address3, "amount": 200}]

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

    inputs = [{"address": address1, "seqNo": mint_seq_no}, {"address": address2, "seqNo": mint_seq_no}]
    outputs = [{"address": address3, "amount": 200}]

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

    inputs = [{"address": address1, "seqNo": mint_seq_no}, {"address": address2, "seqNo": mint_seq_no}]
    outputs = [{"address": address3, "amount": 200}]

    request = helpers.request.transfer(inputs, outputs)

    extra_sig = helpers.wallet.payment_signatures(
        [{"address": address4, "seqNo": mint_seq_no}],
        outputs
    )[0]

    request.operation[SIGS][1] = extra_sig

    assert len(request.operation[SIGS]) == len(inputs)
    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_empty_xfer(helpers):
    inputs = []
    outputs = []
    identifier = "5oXnyuywuz6TvnMDXjjGUm47gToPzdCKZbDvsNdYB4Cy"

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs, identifier=identifier)


def test_invalid_output_numeric_amounts(helpers, addresses, initial_mint):
    """
    Test transfer with different invalid numeric amounts
    """

    [address1, address2, *_] = addresses
    seq_no = get_seq_no(initial_mint)

    inputs = [{ADDRESS: address1, SEQNO: seq_no}]

    # Floats
    outputs = [
        {ADDRESS: address2, AMOUNT: 40.5},
        {ADDRESS: address1, AMOUNT: 59.5}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)

    # None value
    outputs = [
        {ADDRESS: address2, AMOUNT: 100},
        {ADDRESS: address1, AMOUNT: None}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)

    # String number
    outputs = [
        {ADDRESS: address2, AMOUNT: 80},
        {ADDRESS: address1, AMOUNT: "20"}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)

    # Negative Number
    outputs = [
        {ADDRESS: address2, AMOUNT: -50},
        {ADDRESS: address1, AMOUNT: 150}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)

    # Zero value
    outputs = [
        {ADDRESS: address1, AMOUNT: 100},
        {ADDRESS: address2, AMOUNT: 0}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)

    # Output without amount
    request = helpers.request.transfer(inputs, outputs)
    request.operation[OUTPUTS][1].pop(AMOUNT)

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_invalid_input_seq_no(helpers, addresses, initial_mint):
    """
    Test transfer with different invalid numeric seq_no
    """

    [address1, address2, *_] = addresses
    seq_no = get_seq_no(initial_mint)
    outputs = [{ADDRESS: address2, AMOUNT: 100}]

    def _test_invalid_seq_no(seq_no):
        inputs = [{ADDRESS: address1, SEQNO: seq_no}]

        with pytest.raises(RequestNackedException):
            helpers.general.do_transfer(inputs, outputs)

    _test_invalid_seq_no(0)
    _test_invalid_seq_no(-1)
    _test_invalid_seq_no(str(seq_no))
    _test_invalid_seq_no(None)
    _test_invalid_seq_no(1.0)


def test_multiple_inputs_outputs_without_change(
    helpers,
    addresses,
    initial_mint
):
    [address1, address2, address3, address4, address5] = addresses
    mint_seq_no = get_seq_no(initial_mint)

    inputs = [
        {"address": address1, "seqNo": mint_seq_no},
        {"address": address2, "seqNo": mint_seq_no},
        {"address": address3, "seqNo": mint_seq_no},
    ]

    outputs = [
        {"address": address4, "amount": 200},
        {"address": address5, "amount": 100},
    ]

    request = helpers.request.transfer(inputs, outputs)
    response = helpers.sdk.send_and_check_request_objects([request])
    assert response[0][1]["result"]["reqSignature"] != {}
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
        {"address": address4, "seqNo": mint_seq_no, "amount": 100},
        {"address": address4, "seqNo": xfer_seq_no, "amount": 200},
    ]
    assert address5_utxos == [
        {"address": address5, "seqNo": mint_seq_no, "amount": 100},
        {"address": address5, "seqNo": xfer_seq_no, "amount": 100},
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
        {"address": address1, "seqNo": mint_seq_no},
        {"address": address2, "seqNo": mint_seq_no},
        {"address": address3, "seqNo": mint_seq_no},
    ]

    outputs = [
        {"address": address4, "amount": 270},
        {"address": address5, "amount": 10},
        {"address": address1, "amount": 20},
    ]

    request = helpers.request.transfer(inputs, outputs)
    response = helpers.sdk.send_and_check_request_objects([request])
    assert response[0][1]["result"]["reqSignature"] != {}
    result = helpers.sdk.get_first_result(response)
    xfer_seq_no = get_seq_no(result)

    [
        address1_utxos,
        address2_utxos,
        address3_utxos,
        address4_utxos,
        address5_utxos
    ] = helpers.general.get_utxo_addresses(addresses)

    assert address1_utxos == [{"address": address1, "seqNo": xfer_seq_no, "amount": 20}]
    assert address2_utxos == []
    assert address3_utxos == []
    assert address4_utxos == [
        {"address": address4, "seqNo": mint_seq_no, "amount": 100},
        {"address": address4, "seqNo": xfer_seq_no, "amount": 270},
    ]
    assert address5_utxos == [
        {"address": address5, "seqNo": mint_seq_no, "amount": 100},
        {"address": address5, "seqNo": xfer_seq_no, "amount": 10},
    ]
