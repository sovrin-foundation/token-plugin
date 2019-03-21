import json

import pytest
from sovtoken.constants import ADDRESS, AMOUNT, XFER_PUBLIC, SEQNO
from sovtokenfees.constants import FEES
from sovtokenfees.test.test_fees_xfer_txn import send_transfer_request

from plenum.common.txn_util import get_seq_no
from plenum.test import waits
from plenum.test.stasher import delay_rules

from plenum.test.delayers import cDelay
from sovtokenfees.test.helper import check_state, add_fees_request_with_address, \
    get_committed_hash_for_pool, nyms_with_fees, get_amount_from_token_txn

from stp_core.loop.eventually import eventually

from plenum.test.helper import sdk_send_signed_requests, assertExp, sdk_get_and_check_replies

from plenum.test.view_change.helper import ensure_view_change

from plenum.test.test_node import ensureElectionsDone

from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data

from plenum.common.startable import Mode

from plenum.common.constants import DOMAIN_LEDGER_ID, NYM


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


def add_nym_with_fees(helpers, fees, seq_no, looper, addresses, current_amount,
                      check_reply=True):
    seq_no += 1
    nym_with_fees = nyms_with_fees(1,
                                   helpers,
                                   fees,
                                   addresses[0],
                                   current_amount,
                                   init_seq_no=seq_no)[0]
    resp = helpers.sdk.send_request_objects([nym_with_fees])

    if check_reply:
        sdk_get_and_check_replies(looper, resp)

    current_amount -= fees[FEES][NYM]
    return current_amount, seq_no, resp


def send_transfer(helpers, addresses, fees, looper, current_amount, seq_no, check_reply=True):
    seq_no += 1
    transfer_summ = 20
    [address_giver, address_receiver] = addresses
    utxos = [{ADDRESS: address_giver, AMOUNT: current_amount, SEQNO: seq_no}]
    inputs = [{ADDRESS: address_giver, SEQNO: seq_no}]
    outputs = [{ADDRESS: address_receiver, AMOUNT: transfer_summ},
               {ADDRESS: address_giver, AMOUNT: current_amount - transfer_summ - fees[XFER_PUBLIC]}]
    transfer_req = helpers.request.transfer(inputs, outputs)
    transfer_req = helpers.request.add_fees(
        transfer_req,
        utxos,
        fees[XFER_PUBLIC],
        change_address=address_giver
    )

    resp = helpers.sdk.send_request_objects([transfer_req])
    if check_reply:
        sdk_get_and_check_replies(looper, resp)

    current_amount -= (fees[XFER_PUBLIC] + transfer_summ)
    return current_amount, seq_no, resp


def test_revert_works_for_fees_after_view_change(looper, helpers,
                                                 nodeSetWithIntegratedTokenPlugin,
                                                 sdk_pool_handle,
                                                 sdk_wallet_trustee,
                                                 fees_set,
                                                 mint_tokens, addresses, fees):
    node_set = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = 0
    reverted_node = nodeSetWithIntegratedTokenPlugin[-1]

    current_amount, seq_no, _ = add_nym_with_fees(helpers, fees_set, seq_no, looper, addresses, current_amount)
    current_amount, seq_no, _ = send_transfer(helpers, addresses, fees, looper, current_amount, seq_no)

    with delay_rules(reverted_node.nodeIbStasher, cDelay()):
        current_amount, seq_no, _ = send_transfer(helpers, addresses, fees, looper, current_amount, seq_no)
        len_batches_before = len(reverted_node.master_replica.batches)
        current_amount, seq_no, _ = add_nym_with_fees(helpers, fees_set, seq_no, looper, addresses, current_amount)
        looper.runFor(waits.expectedPrePrepareTime(len(nodeSetWithIntegratedTokenPlugin)))
        len_batches_after = len(reverted_node.master_replica.batches)

        """
        Checks, that we have a 2 new batches
        """
        assert len_batches_after - len_batches_before == 1
        for n in node_set:
            n.view_changer.on_master_degradation()
        ensure_view_change(looper, nodeSetWithIntegratedTokenPlugin)

        looper.run(eventually(lambda: assertExp(reverted_node.mode == Mode.participating)))
    ensure_all_nodes_have_same_data(looper, node_set)

    add_nym_with_fees(helpers, fees_set, 5, sdk_pool_handle, looper, addresses, current_amount)
    ensure_all_nodes_have_same_data(looper, node_set)
