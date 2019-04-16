import pytest

from indy_common.constants import NYM

from sovtoken.constants import XFER_PUBLIC

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change


def fees():
    return {NYM: 0, XFER_PUBLIC: 0}  # no fees


def test_xfer_fees_nym_during_view_change(
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

    scenario_txns_during_view_change(looper, nodeSetWithIntegratedTokenPlugin, send_txns, curr_utxo)
