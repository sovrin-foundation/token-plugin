import pytest

from sovtokenfees.test.constants import NYM_FEES_ALIAS

from sovtokenfees.test.helper import InputsStrategy, OutputsStrategy
from sovtokenfees.test.conftest import IOAddressesStatic


ADDRESSES_NUM = 3
MINT_UTXOS_NUM = 1
MINT_AMOUNT = 1000


@pytest.fixture
def fees(request):
    marker = request.node.get_closest_marker('nym_fee')
    return {
        NYM_FEES_ALIAS: marker.args[0] if marker else 4
    }


@pytest.fixture
def io_addresses(request, addresses):
    marker = request.node.get_closest_marker('io_border')
    assert marker
    io_border = marker.args[0]
    return IOAddressesStatic(
        addresses[:io_border], addresses[io_border:]
    )


@pytest.fixture
def inputs_strategy(request):
    return InputsStrategy.all_utxos


@pytest.fixture
def outputs_strategy(request):
    return OutputsStrategy.transfer_all_equal


@pytest.mark.io_border(ADDRESSES_NUM)
@pytest.mark.nym_fee(ADDRESSES_NUM * MINT_UTXOS_NUM * MINT_AMOUNT)
def test_nym_with_no_change_no_outputs(
    nodeSetWithIntegratedTokenPlugin,
    fees_set,
    mint_multiple_tokens,
    send_and_check_nym,
):
    send_and_check_nym()


@pytest.mark.io_border(ADDRESSES_NUM - 1)
def test_nym_with_output_not_in_inputs(
    nodeSetWithIntegratedTokenPlugin,
    fees_set,
    mint_multiple_tokens,
    send_and_check_nym,
):
    send_and_check_nym()
