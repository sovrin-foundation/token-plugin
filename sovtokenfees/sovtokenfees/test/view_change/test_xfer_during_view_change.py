import pytest

from sovtoken.constants import XFER_PUBLIC

from sovtokenfees.test.conftest import MintStrategy

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change_new

ADDRESSES_NUM = 4
MINT_STRATEGY = MintStrategy.multiple_equal
MINT_UTXOS_NUM = 3


@pytest.fixture(
    scope='module',
    params=[
        {XFER_PUBLIC: 0},  # no fees
        {XFER_PUBLIC: 4},  # with fees
    ], ids=lambda x: 'fees' if x[XFER_PUBLIC] else 'nofees'
)
def fees(request):
    return request.param


def test_xfer_during_view_change(
        looper,
        helpers,
        nodeSetWithIntegratedTokenPlugin,
        fees_set,
        mint_multiple_tokens,
        send_and_check_xfer,
        io_addresses
):
    scenario_txns_during_view_change_new(
        looper,
        helpers,
        nodeSetWithIntegratedTokenPlugin,
        io_addresses(),
        send_and_check_xfer
    )
