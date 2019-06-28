import pytest

from plenum.common.exceptions import RequestRejectedException
from plenum.test.pool_transactions.helper import sdk_add_new_nym

from indy_common.constants import NYM
from sovtokenfees.test.constants import NYM_FEES_ALIAS

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change

from sovtokenfees.test.helper import InputsStrategy


MINT_UTXOS_NUM = 6
INPUTS_STRATEGY = InputsStrategy.first_utxo_only


@pytest.fixture(
    scope='module',
    params=[
        {NYM_FEES_ALIAS: 4},  # with fees
        {NYM_FEES_ALIAS: 0},  # no fees
    ], ids=lambda x: 'fees' if x[NYM_FEES_ALIAS] else 'nofees'
)
def fees(request):
    return request.param


def test_nym_fees_during_view_change(
        looper,
        helpers,
        nodeSetWithIntegratedTokenPlugin,
        fees,
        fees_set,
        mint_multiple_tokens,
        send_and_check_nym,
        io_addresses,
        sdk_pool_handle,
        sdk_wallet_client
):
    def send_txns_invalid():
        with pytest.raises(RequestRejectedException, match='Rule for this action is'):
            sdk_add_new_nym(looper, sdk_pool_handle, sdk_wallet_client)

    scenario_txns_during_view_change(
        looper,
        helpers,
        nodeSetWithIntegratedTokenPlugin,
        io_addresses,
        send_and_check_nym,
        send_txns_invalid=(None if fees[NYM_FEES_ALIAS] else send_txns_invalid)
    )
