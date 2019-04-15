import pytest

from plenum.common.exceptions import RequestRejectedException

from sovtokenfees.test.view_change.helper import scenario_txns_during_view_change


def test_nym_during_view_change(
        looper,
        nodeSetWithIntegratedTokenPlugin,

        fees_set,
        curr_utxo,
        send_and_check_nym_with_fees_curr_utxo
):
    def send_nym(invalid=False):
        if invalid:
            with pytest.raises(RequestRejectedException, match='Insufficient funds'):
                curr_utxo['amount'] += 1
                send_and_check_nym_with_fees_curr_utxo()
        else:
            send_and_check_nym_with_fees_curr_utxo()

    scenario_txns_during_view_change(looper, nodeSetWithIntegratedTokenPlugin, send_nym)
