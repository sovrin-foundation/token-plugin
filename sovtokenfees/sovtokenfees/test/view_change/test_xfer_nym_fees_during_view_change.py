import pytest
from sovtokenfees.test.constants import NYM_FEES_ALIAS, XFER_PUBLIC_FEES_ALIAS

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change


ADDRESSES_NUM = 2
MINT_UTXOS_NUM = 1


@pytest.fixture(
    scope='module',
    params=[
        {NYM_FEES_ALIAS: 4, XFER_PUBLIC_FEES_ALIAS: 0},   # no fees for XFER_PUBLIC
        {NYM_FEES_ALIAS: 0, XFER_PUBLIC_FEES_ALIAS: 8},   # no fees for NYM
        {NYM_FEES_ALIAS: 4, XFER_PUBLIC_FEES_ALIAS: 8},   # fees for both
        {NYM_FEES_ALIAS: 0, XFER_PUBLIC_FEES_ALIAS: 0},   # no fees
    ], ids=lambda x: '-'.join(sorted([k for k, v in x.items() if v])) or 'nofees'
)
def fees(request):
    return request.param


def test_xfer_nym_fees_during_view_change(
        looper,
        nodeSetWithIntegratedTokenPlugin,
        fees_set,
        curr_utxo,
        send_and_check_transfer_curr_utxo,
        send_and_check_nym_with_fees_curr_utxo,
):
    def send_txns():
        send_and_check_transfer_curr_utxo()
        send_and_check_nym_with_fees_curr_utxo()

    scenario_txns_during_view_change(looper, nodeSetWithIntegratedTokenPlugin, curr_utxo, send_txns)
