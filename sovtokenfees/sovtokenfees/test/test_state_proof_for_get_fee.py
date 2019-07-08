from common.serializers.json_serializer import JsonSerializer
from sovtokenfees.domain import build_path_for_set_fees

from plenum.test.txn_author_agreement.helper import check_state_proof
from sovtokenfees.test.constants import NYM_FEES_ALIAS

from plenum.test.delayers import cDelay

from plenum.test.stasher import delay_rules


def test_state_proof_for_get_fee(looper, helpers,
                                 nodeSetWithIntegratedTokenPlugin,
                                 sdk_pool_handle):
    fees_1 = {NYM_FEES_ALIAS: 1}
    fees_2 = {NYM_FEES_ALIAS: 2}
    node_set = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]

    helpers.general.do_set_fees(fees_1)
    response1 = helpers.general.do_get_fees()
    check_state_proof(response1, build_path_for_set_fees(),
                      JsonSerializer().serialize(fees_1))

    config_state = nodeSetWithIntegratedTokenPlugin[0].states[2]
    assert config_state.headHash == config_state.committedHeadHash

    # We delay commit messages to get different committed and uncommitted roots for ledger
    with delay_rules(node_set, cDelay()):
        helpers.general.set_fees_without_waiting(fees_2)
        looper.runFor(3)
        response2 = helpers.general.do_get_fees()
        # Returned state proof for first set_fees, which is committed
        check_state_proof(response2, build_path_for_set_fees(),
                          JsonSerializer().serialize(fees_1))
        # Let's check that uncommitted state differs from committed
        assert config_state.headHash != config_state.committedHeadHash
