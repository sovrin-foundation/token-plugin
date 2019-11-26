import pytest
from sovtokenfees.constants import FEES
from sovtokenfees.test.constants import NYM_FEES_ALIAS

from plenum.common.constants import STATE_PROOF

from plenum.test.stasher import delay_rules

from plenum.test.delayers import req_delay
from sovtokenfees.test.helper import send_and_check_auth_rule


@pytest.mark.skip
def test_state_proof_for_get_fees(helpers, nodeSetWithIntegratedTokenPlugin,
                                  looper, sdk_pool_handle, sdk_wallet_trustee):
    # make sure that config ledger is BLS signed by sending a txn to config ledger
    send_and_check_auth_rule(looper, sdk_pool_handle, sdk_wallet_trustee)
    with delay_rules([n.clientIbStasher for n in nodeSetWithIntegratedTokenPlugin[1:]], req_delay()):
        resp = helpers.general.do_get_fees()
        assert resp.get(STATE_PROOF, False)
        assert {} == resp[FEES]

    fees = {NYM_FEES_ALIAS: 5}
    helpers.general.do_set_fees(fees)
    with delay_rules([n.clientIbStasher for n in nodeSetWithIntegratedTokenPlugin[1:]], req_delay()):
        resp = helpers.general.do_get_fees()
        assert resp.get(STATE_PROOF, False)
        assert fees == resp[FEES]
