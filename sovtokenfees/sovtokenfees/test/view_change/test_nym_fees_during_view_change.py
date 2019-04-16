from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change

from indy_common.constants import NYM


def fees():
    return {NYM: 4}  # fees set


def test_nym_fees_during_view_change(
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
