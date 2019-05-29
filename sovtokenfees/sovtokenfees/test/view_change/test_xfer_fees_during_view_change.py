import pytest
from sovtokenfees.test.constants import XFER_PUBLIC_FEES_ALIAS

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change


ADDRESSES_NUM = 2
MINT_UTXOS_NUM = 1


@pytest.fixture(
    scope='module',
    params=[
        {XFER_PUBLIC_FEES_ALIAS: 4},  # with fees
        {XFER_PUBLIC_FEES_ALIAS: 0},  # no fees
    ], ids=lambda x: 'fees' if x[XFER_PUBLIC_FEES_ALIAS] else 'nofees'
)
def fees(request):
    return request.param


def test_xfer_fees_during_view_change(
        looper,
        nodeSetWithIntegratedTokenPlugin,
        fees_set,
        curr_utxo,
        send_and_check_transfer_curr_utxo
):
    scenario_txns_during_view_change(
        looper,
        nodeSetWithIntegratedTokenPlugin,
        curr_utxo,
        send_and_check_transfer_curr_utxo
    )
