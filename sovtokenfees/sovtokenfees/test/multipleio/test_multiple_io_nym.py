import pytest

from indy_common.constants import NYM
from sovtokenfees.test.constants import NYM_FEES_ALIAS


@pytest.fixture(
    scope='module',
    params=[
        {NYM_FEES_ALIAS: 4},  # with fees
    ], ids=lambda x: 'fees' if x[NYM_FEES_ALIAS] else 'nofees'
)
def fees(request):
    return request.param


def test_nym_with_multiple_io(
    nodeSetWithIntegratedTokenPlugin,
    fees_set,
    mint_multiple_tokens,
    io_addresses,
    outputs_strategy,
    send_and_check_nym,
):
    send_and_check_nym()
    io_addresses.rotate()
    send_and_check_nym()
