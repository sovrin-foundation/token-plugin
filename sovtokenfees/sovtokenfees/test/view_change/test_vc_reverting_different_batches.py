import pytest
from sovtoken.constants import ADDRESS, AMOUNT

from plenum.common.txn_util import get_seq_no
from plenum.test import waits
from plenum.test.stasher import delay_rules, delay_rules_without_processing
from plenum.test.delayers import cDelay, pDelay
from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_nym_with_fees, send_and_check_transfer, \
    ensure_all_nodes_have_same_data
from stp_core.loop.eventually import eventually
from plenum.test.helper import assertExp, sdk_get_and_check_replies
from plenum.test.view_change.helper import ensure_view_change, ensure_view_change_complete
from plenum.common.startable import Mode


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def test_revert_works_for_fees_after_view_change(looper, helpers,
                                                 nodeSetWithIntegratedTokenPlugin,
                                                 sdk_pool_handle,
                                                 fees_set,
                                                 mint_tokens, addresses, fees):
    node_set = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = get_seq_no(mint_tokens)
    reverted_node = nodeSetWithIntegratedTokenPlugin[-1]

    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount)
    current_amount, seq_no, _ = send_and_check_transfer(helpers, addresses, fees, looper, current_amount, seq_no)

    with delay_rules_without_processing(reverted_node.nodeIbStasher, cDelay()):
        len_batches_before = len(reverted_node.master_replica.batches)
        current_amount, seq_no, _ = send_and_check_transfer(helpers, addresses, fees, looper, current_amount, seq_no)
        current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                                 current_amount)
        looper.runFor(waits.expectedPrePrepareTime(len(nodeSetWithIntegratedTokenPlugin)))
        len_batches_after = len(reverted_node.master_replica.batches)

        """
        Checks, that we have a 2 new batches
        """
        assert len_batches_after - len_batches_before == 2
        for n in node_set:
            n.view_changer.on_master_degradation()
        ensure_view_change(looper, nodeSetWithIntegratedTokenPlugin)

        looper.run(eventually(lambda: assertExp(reverted_node.mode == Mode.participating)))
    ensure_all_nodes_have_same_data(looper, node_set)

    send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses, current_amount)
    ensure_all_nodes_have_same_data(looper, node_set)


@pytest.mark.skip(reason="requestQueues doesn't guarantee the order of requests after view_change")
def test_revert_for_all_after_view_change(looper, helpers,
                                          nodeSetWithIntegratedTokenPlugin,
                                          sdk_pool_handle,
                                          fees_set,
                                          mint_tokens, addresses, fees):
    node_set = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = get_seq_no(mint_tokens)
    reverted_node = nodeSetWithIntegratedTokenPlugin[-1]

    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount)
    current_amount, seq_no, _ = send_and_check_transfer(helpers, addresses, fees, looper, current_amount, seq_no)

    ensure_all_nodes_have_same_data(looper, node_set)

    with delay_rules([n.nodeIbStasher for n in node_set], cDelay(), pDelay()):
        len_batches_before = len(reverted_node.master_replica.batches)
        current_amount, seq_no, resp1 = send_and_check_transfer(helpers, addresses, fees, looper, current_amount,
                                                                seq_no, check_reply=False)
        current_amount, seq_no, resp2 = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                                     current_amount, check_reply=False)
        looper.runFor(waits.expectedPrePrepareTime(len(nodeSetWithIntegratedTokenPlugin)))
        len_batches_after = len(reverted_node.master_replica.batches)

        """
        Checks, that we have a 2 new batches
        """
        assert len_batches_after - len_batches_before == 2
        for n in node_set:
            n.view_changer.on_master_degradation()
        ensure_view_change_complete(looper, nodeSetWithIntegratedTokenPlugin)

        looper.run(eventually(lambda: assertExp(reverted_node.mode == Mode.participating)))
    ensure_all_nodes_have_same_data(looper, node_set)
    sdk_get_and_check_replies(looper, resp1)
    sdk_get_and_check_replies(looper, resp2)
    send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses, current_amount)
    ensure_all_nodes_have_same_data(looper, node_set)
