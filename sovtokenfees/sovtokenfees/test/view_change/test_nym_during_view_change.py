import pytest

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change

from indy_common.constants import NYM


@pytest.fixture(
    scope='module',
    params=[
        {NYM: 0},  # no fees
        {NYM: 4},  # with fees
    ], ids=lambda x: 'fees' if x[NYM] else 'nofees'
)
def fees(request):
    return request.param


def test_nym_during_view_change(
        looper,
        nodeSetWithIntegratedTokenPlugin,
        fees_set,
        curr_utxo,
        send_and_check_nym_with_fees_curr_utxo
):
    scenario_txns_during_view_change(
        looper,
        nodeSetWithIntegratedTokenPlugin,
        send_and_check_nym_with_fees_curr_utxo,
        curr_utxo
    )
