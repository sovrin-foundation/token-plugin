import pytest
from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay

from plenum.test.helper import assertExp, sdk_get_and_check_replies

from plenum.common.constants import CONFIG_LEDGER_ID


def get_fees(node):
    fee_req_handler = node.ledger_to_req_handler.get(CONFIG_LEDGER_ID)
    return fee_req_handler.fees


@pytest.mark.skip(reason="ST-504")
def test_revert_fees_reset(looper, helpers,
                           nodeSetWithIntegratedTokenPlugin,
                           address_main, mint_tokens,
                           fees):
    node_set = nodeSetWithIntegratedTokenPlugin
    reverted_node = node_set[-1]
    fees_before = get_fees(reverted_node)
    with delay_rules(reverted_node.nodeIbStasher, cDelay()):
        """
        Unset fees for pool
        """
        set_fees = helpers.general.set_fees_without_waiting(fees)
        sdk_get_and_check_replies(looper, set_fees)
        reverted_node.master_replica.revert_unordered_batches()
    fees_after = get_fees(reverted_node)
    assert fees_after == fees_before
