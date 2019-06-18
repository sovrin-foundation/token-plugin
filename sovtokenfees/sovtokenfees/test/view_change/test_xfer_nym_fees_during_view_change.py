import pytest
from sovtokenfees.test.constants import (
    NYM_FEES_ALIAS, XFER_PUBLIC_FEES_ALIAS, alias_to_txn_type
)

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change


@pytest.fixture(
    scope='module',
    params=[
        {NYM_FEES_ALIAS: 4, XFER_PUBLIC_FEES_ALIAS: 0},   # no fees for XFER_PUBLIC
        {NYM_FEES_ALIAS: 0, XFER_PUBLIC_FEES_ALIAS: 8},   # no fees for NYM
        {NYM_FEES_ALIAS: 4, XFER_PUBLIC_FEES_ALIAS: 8},   # fees for both
        {NYM_FEES_ALIAS: 0, XFER_PUBLIC_FEES_ALIAS: 0},   # no fees
    ], ids=lambda x: '-'.join(sorted([alias_to_txn_type[k] for k, v in x.items() if v])) or 'nofees'
)
def fees(request):
    return request.param


def test_xfer_nym_fees_during_view_change(
        looper,
        helpers,
        nodeSetWithIntegratedTokenPlugin,
        fees_set,
        mint_multiple_tokens,
        send_and_check_xfer,
        send_and_check_nym,
        io_addresses
):
    def send_txns():
        send_and_check_xfer()
        send_and_check_nym()

    scenario_txns_during_view_change(
        looper,
        helpers,
        nodeSetWithIntegratedTokenPlugin,
        io_addresses,
        send_txns
    )
