from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change

# no fees for XFER_PUBLIC
TXN_FEES = {}


def test_xfer_during_view_change(
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
