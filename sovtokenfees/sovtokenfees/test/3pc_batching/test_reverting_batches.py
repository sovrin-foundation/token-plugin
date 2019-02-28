import json

from plenum.test.delayers import cDelay

from plenum.test.stasher import delay_rules
from sovtoken import TOKEN_LEDGER_ID
from sovtokenfees.test.helper import add_fees_request_with_address, get_head_hash_for_pool, \
    get_uncommitted_txns_count_for_pool

from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies, sdk_send_random_and_check

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data

from plenum.test.pool_transactions.helper import sdk_add_new_nym

from plenum.test import waits


def test_revert_batches_with_fees_unset_fees_without_fee(looper, helpers,
                                                         nodeSetWithIntegratedTokenPlugin,
                                                         sdk_pool_handle,
                                                         sdk_wallet_trustee,
                                                         sdk_wallet_steward,
                                                         fees_set, address_main, mint_tokens):
    node_set = nodeSetWithIntegratedTokenPlugin
    reverted_node = node_set[-1]

    head_hash_before = get_head_hash_for_pool([reverted_node], TOKEN_LEDGER_ID)
    uncommitted_size_before = get_uncommitted_txns_count_for_pool([reverted_node], TOKEN_LEDGER_ID)

    with delay_rules(reverted_node.nodeIbStasher, cDelay()):
        request_check_health = helpers.request.nym()
        request_check_health = add_fees_request_with_address(
            helpers,
            fees_set,
            request_check_health,
            address_main
        )
        r = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(request_check_health.as_dict)])
        looper.runFor(waits.expectedPrePrepareTime(len(node_set)))
        """
        We send only 1 txn with fees, and expects, 
        that we have only 1 uncommitted txn for token_ledger
        """
        assert get_uncommitted_txns_count_for_pool([reverted_node], TOKEN_LEDGER_ID) - uncommitted_size_before == 1
        sdk_get_and_check_replies(looper, r)
        assert get_uncommitted_txns_count_for_pool([reverted_node], TOKEN_LEDGER_ID) - uncommitted_size_before == 1
        """
        Unset fees, for sending txn without fees
        """
        helpers.node.reset_fees()
        sdk_add_new_nym(looper, sdk_pool_handle, sdk_wallet_steward)
        """
        We sent a NYM txn without fees and expects, 
        that count of uncommitted txns wasn`t changed
        """
        assert get_uncommitted_txns_count_for_pool([reverted_node], TOKEN_LEDGER_ID) - uncommitted_size_before == 1
        """
        Initiate reverting procedure by calling start_catchup
        """
        reverted_node.master_replica.revert_unordered_batches()
        head_hash_after = get_head_hash_for_pool([reverted_node], TOKEN_LEDGER_ID)
    uncommitted_size_after = get_uncommitted_txns_count_for_pool([reverted_node], TOKEN_LEDGER_ID)
    assert head_hash_before == head_hash_after
    assert uncommitted_size_before == uncommitted_size_after