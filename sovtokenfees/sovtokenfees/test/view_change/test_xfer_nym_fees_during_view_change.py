import pytest

from indy_common.constants import NYM

from sovtoken.constants import XFER_PUBLIC

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change


@pytest.fixture(
    scope='module',
    params=[
        {NYM: 4, XFER_PUBLIC: 0},   # no fees for XFER_PUBLIC
        {NYM: 0, XFER_PUBLIC: 8},   # no fees for NYM
        {NYM: 4, XFER_PUBLIC: 8},   # fees for both
        {NYM: 0, XFER_PUBLIC: 0},   # no fees
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
