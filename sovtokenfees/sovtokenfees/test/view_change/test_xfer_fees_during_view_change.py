from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change

from sovtoken.constants import XFER_PUBLIC


def fees():
    return {XFER_PUBLIC: 8}  # fees set


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
        send_and_check_transfer_curr_utxo,
        curr_utxo
    )
