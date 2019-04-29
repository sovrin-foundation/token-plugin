import pytest

from plenum.common.exceptions import RequestRejectedException
from plenum.test.pool_transactions.helper import sdk_add_new_nym

from indy_common.constants import NYM

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change


ADDRESSES_NUM = 2
MINT_UTXOS_NUM = 1


@pytest.fixture(
    scope='module',
    params=[
        {NYM: 4},  # with fees
        {NYM: 0},  # no fees
    ], ids=lambda x: 'fees' if x[NYM] else 'nofees'
)
def fees(request):
    return request.param


def test_nym_fees_during_view_change(
        looper,
        nodeSetWithIntegratedTokenPlugin,
        sdk_pool_handle, sdk_wallet_client,
        fees,
        fees_set,
        curr_utxo,
        send_and_check_nym_with_fees_curr_utxo
):
    def send_txns_invalid():
        with pytest.raises(RequestRejectedException, match='Rule for this action is'):
            sdk_add_new_nym(looper, sdk_pool_handle, sdk_wallet_client)

    scenario_txns_during_view_change(
        looper,
        nodeSetWithIntegratedTokenPlugin,
        curr_utxo,
        send_and_check_nym_with_fees_curr_utxo,
        send_txns_invalid=(None if fees[NYM] else send_txns_invalid)
    )
