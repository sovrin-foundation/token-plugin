import pytest
from sovtoken.request_handlers.token_utils import create_state_key

from plenum.common.txn_util import get_seq_no
from plenum.common.exceptions import RequestNackedException
from plenum.common.types import OPERATION
from sovtoken.constants import SIGS, ADDRESS, SEQNO, AMOUNT, OUTPUTS, PAYMENT_ADDRESS, TOKEN_LEDGER_ID, INPUTS
from sovtoken.test.helper import user1_token_wallet, libsovtoken_address_to_address


@pytest.fixture
def addresses(helpers):
    return helpers.wallet.create_new_addresses(5)

@pytest.fixture
def addresses_inner(helpers):
    return helpers.inner.wallet.create_new_addresses(5)


@pytest.fixture
def initial_mint(helpers, addresses):
    outputs = [{"address": address, "amount": 100} for address in addresses]
    mint_request = helpers.request.mint(outputs)
    responses = helpers.sdk.send_and_check_request_objects([mint_request])
    result = helpers.sdk.get_first_result(responses)
    return result

@pytest.fixture
def initial_mint_inner(helpers, addresses_inner):
    outputs = [{"address": "pay:sov:" + address, "amount": 100} for address in addresses_inner]
    mint_request = helpers.request.mint(outputs)
    responses = helpers.sdk.send_and_check_request_objects([mint_request])
    result = helpers.sdk.get_first_result(responses)
    return result


def test_state_after_xfer(helpers, initial_mint, addresses, nodeSetWithIntegratedTokenPlugin):

    mint_seq_no = get_seq_no(initial_mint)
    [address1, address2, *_] = addresses

    inputs = helpers.general.get_utxo_addresses([address1])
    inputs = [utxo for utxos in inputs for utxo in utxos]
    outputs = [{"address": address2, "amount": 100}]

    helpers.general.do_transfer(inputs, outputs)
    key = create_state_key(libsovtoken_address_to_address(address1), mint_seq_no)

    for n in nodeSetWithIntegratedTokenPlugin:
        res = n.db_manager.get_state(TOKEN_LEDGER_ID).get(key)
        assert not res


def test_multiple_inputs_with_1_incorrect_input_sig(  # noqa
    helpers,
    addresses,
    initial_mint,
):
    mint_seq_no = get_seq_no(initial_mint)
    [address1, address2, address3, *_] = addresses

    # Multiple inputs are used in a transaction but one of the inputs
    # has incorrect signature
    inputs = helpers.general.get_utxo_addresses([address1, address2])
    inputs = [utxo for utxos in inputs for utxo in utxos]
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

    inputs = helpers.general.get_utxo_addresses([address1, address2])
    inputs = [utxo for utxos in inputs for utxo in utxos]
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
    [address1, address2, address3, *_] = addresses
    address4 = helpers.inner.wallet.create_address()
    inputs = helpers.general.get_utxo_addresses([address1, address2])
    inputs = [utxo for utxos in inputs for utxo in utxos]
    outputs = [{"address": address3, "amount": 200}]

    request = helpers.request.transfer(inputs, outputs)

    extra_sig = helpers.inner.wallet.payment_signatures(
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
        helpers.inner.general.do_transfer(inputs, outputs, identifier=identifier)


def test_invalid_output_numeric_amounts(helpers, addresses_inner, initial_mint_inner):
    """
    Test transfer with different invalid numeric amounts
    """

    [address1, address2, *_] = addresses_inner
    seq_no = get_seq_no(initial_mint_inner)

    inputs = [{ADDRESS: address1, SEQNO: seq_no}]

    # Floats
    outputs = [
        {ADDRESS: address2, AMOUNT: 40.5},
        {ADDRESS: address1, AMOUNT: 59.5}
    ]

    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_transfer(inputs, outputs)

    # None value
    outputs = [
        {ADDRESS: address2, AMOUNT: 100},
        {ADDRESS: address1, AMOUNT: None}
    ]

    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_transfer(inputs, outputs)

    # String number
    outputs = [
        {ADDRESS: address2, AMOUNT: 80},
        {ADDRESS: address1, AMOUNT: "20"}
    ]

    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_transfer(inputs, outputs)

    # Negative Number
    outputs = [
        {ADDRESS: address2, AMOUNT: -50},
        {ADDRESS: address1, AMOUNT: 150}
    ]

    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_transfer(inputs, outputs)

    # Zero value
    outputs = [
        {ADDRESS: address1, AMOUNT: 100},
        {ADDRESS: address2, AMOUNT: 0}
    ]

    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_transfer(inputs, outputs)

    # Output without amount
    request = helpers.inner.request.transfer(inputs, outputs)
    request.operation[OUTPUTS][1].pop(AMOUNT)

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_invalid_input_seq_no(helpers, addresses_inner, initial_mint_inner):
    """
    Test transfer with different invalid numeric seq_no
    """

    [address1, address2, *_] = addresses_inner
    seq_no = get_seq_no(initial_mint_inner)
    outputs = [{ADDRESS: address2, AMOUNT: 100}]

    def _test_invalid_seq_no(seq_no):
        inputs = [{ADDRESS: address1, SEQNO: seq_no}]

        with pytest.raises(RequestNackedException):
            helpers.inner.general.do_transfer(inputs, outputs)

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

    inputs = helpers.general.get_utxo_addresses([address1, address2, address3])
    inputs = [utxo for utxos in inputs for utxo in utxos]

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
    assert address4_utxos[0][PAYMENT_ADDRESS] == address4
    assert address4_utxos[1][PAYMENT_ADDRESS] == address4
    assert address4_utxos[0][AMOUNT] == 100
    assert address4_utxos[1][AMOUNT] == 200
    assert address5_utxos[0][PAYMENT_ADDRESS] == address5
    assert address5_utxos[1][PAYMENT_ADDRESS] == address5
    assert address5_utxos[0][AMOUNT] == 100
    assert address5_utxos[1][AMOUNT] == 100


def test_multiple_inputs_outputs_with_change(
    helpers,
    addresses,
    initial_mint,
    user1_token_wallet,
):
    [address1, address2, address3, address4, address5] = addresses
    mint_seq_no = get_seq_no(initial_mint)

    inputs = helpers.general.get_utxo_addresses([address1, address2, address3])
    inputs = [utxo for utxos in inputs for utxo in utxos]

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

    assert address1_utxos[0][PAYMENT_ADDRESS] == address1
    assert address1_utxos[0][AMOUNT] == 20
    assert address2_utxos == []
    assert address3_utxos == []
    assert address4_utxos[0][PAYMENT_ADDRESS] == address4
    assert address4_utxos[1][PAYMENT_ADDRESS] == address4
    assert address4_utxos[0][AMOUNT] == 100
    assert address4_utxos[1][AMOUNT] == 270
    assert address5_utxos[0][PAYMENT_ADDRESS] == address5
    assert address5_utxos[1][PAYMENT_ADDRESS] == address5
    assert address5_utxos[0][AMOUNT] == 100
    assert address5_utxos[1][AMOUNT] == 10


def test_xfer_signatures_included_in_txn(
        helpers,
        addresses,
        initial_mint
):
    [address1, address2, address3, address4, address5] = addresses

    inputs = helpers.general.get_utxo_addresses([address1, address2, address3])
    inputs = [utxo for utxos in inputs for utxo in utxos]

    outputs = [
        {"address": address4, "amount": 200},
        {"address": address5, "amount": 100},
    ]

    request = helpers.request.transfer(inputs, outputs)
    response = helpers.sdk.send_and_check_request_objects([request])

    sigs = [(i["address"], s) for i, s in zip(request.operation[INPUTS], request.operation[SIGS])]
    request = response[0][0]
    sigs.append((request["identifier"], request["signature"]))

    rep_sigs = [(v['from'], v['value']) for v in response[0][1]["result"]["reqSignature"]["values"]]

    assert sorted(rep_sigs) == sorted(sigs)
