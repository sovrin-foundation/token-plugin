import pytest

from sovtokenfees.test.constants import XFER_PUBLIC_FEES_ALIAS

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change


@pytest.fixture(
    scope='module',
    params=[
        {XFER_PUBLIC_FEES_ALIAS: 0},  # no fees
        {XFER_PUBLIC_FEES_ALIAS: 4},  # with fees
    ], ids=lambda x: 'fees' if x[XFER_PUBLIC_FEES_ALIAS] else 'nofees'
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
    scenario_txns_during_view_change(
        looper,
        helpers,
        nodeSetWithIntegratedTokenPlugin,
        io_addresses,
        send_and_check_xfer
    )
