import pytest
from sovtoken.constants import ADDRESS, SEQNO, AMOUNT, XFER_PUBLIC
from sovtokenfees.test.helper import ensure_all_nodes_have_same_data, get_amount_from_token_txn, \
    send_and_check_nym_with_fees, send_and_check_transfer, check_state

from plenum.common.constants import NYM
from plenum.common.txn_util import get_seq_no
from plenum.test.conftest import getValueFromModule

from plenum.test.stasher import delay_rules, delay_rules_without_processing

from plenum.test.delayers import pDelay, cDelay

from plenum.test import waits

from stp_core.loop.eventually import eventually

from plenum.test.helper import assertExp

from plenum.common.startable import Mode


def test_revert_nym_with_fees_before_catchup(looper, helpers,
                                                  nodeSetWithIntegratedTokenPlugin,
                                                  fees_set, fees,
                                                  xfer_mint_tokens, xfer_addresses):
    nodes = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(xfer_mint_tokens)
    seq_no = get_seq_no(xfer_mint_tokens)
    lagging_node = nodes[-1]
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, xfer_addresses,
                                                             current_amount)
    with delay_rules_without_processing(lagging_node.nodeIbStasher, cDelay(), pDelay()):
        current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, xfer_addresses,
                                                                 current_amount)
        looper.runFor(waits.expectedPrePrepareTime(len(nodes)))
        lagging_node.start_catchup()
        for n in nodes:
            looper.run(eventually(lambda: assertExp(n.mode == Mode.participating)))
        for n in nodes:
            looper.run(eventually(check_state, n, True, retryWait=0.2, timeout=15))
    ensure_all_nodes_have_same_data(looper, nodes)
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, xfer_addresses,
                                                             current_amount)
    ensure_all_nodes_have_same_data(looper, nodes)
