from indy_common.constants import CONFIG_LEDGER_ID

from plenum.common.constants import AUDIT_LEDGER_ID
from sovtokenfees.constants import FEES
from sovtokenfees.domain import build_path_for_set_fees
from sovtokenfees.fees_authorizer import FeesAuthorizer
from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler

from stp_core.loop.eventually import eventually

from plenum.test.txn_author_agreement.helper import check_state_proof

from state.pruning_state import PruningState

from storage.kv_in_memory import KeyValueStorageInMemory


def test_get_fees_when_no_fees_set(helpers, looper):
    def _freshness_done():
        assert audit_ledger.size == length_after + 1

    for n in helpers.node._nodes:
        curr_state = n.states[CONFIG_LEDGER_ID]
        curr_state.remove(build_path_for_set_fees().encode())
    """
    Update config state
    """
    primary = helpers.node.get_primary_node()
    audit_ledger = primary.getLedger(AUDIT_LEDGER_ID)
    length_after = audit_ledger.size
    primary.master_replica._do_send_3pc_batch(ledger_id=CONFIG_LEDGER_ID)
    looper.run(eventually(_freshness_done))
    """
    GET_FEES
    """
    response = helpers.general.do_get_fees()
    ledger_fees = response[FEES]
    assert ledger_fees == {}
    check_state_proof(response, build_path_for_set_fees(), None)
    helpers.node.assert_set_fees_in_memory({})