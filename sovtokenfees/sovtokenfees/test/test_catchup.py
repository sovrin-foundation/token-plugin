import pytest

from plenum.common.config_helper import PNodeConfigHelper
from plenum.common.constants import NYM
from plenum.common.txn_util import get_seq_no
from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data
from plenum.test.test_node import TestNode
from sovtoken.constants import (ADDRESS, AMOUNT, SEQNO, TOKEN_LEDGER_ID,
                                XFER_PUBLIC)
from sovtoken.main import \
    integrate_plugin_in_node as integrate_token_plugin_in_node
from sovtoken.test.helper import user1_token_wallet
from sovtokenfees.main import \
    integrate_plugin_in_node as integrate_fees_plugin_in_node
from sovtokenfees.test.test_fees_non_xfer_txn import (address_main,
                                                      mint_tokens, pay_fees)

TestRunningTimeLimitSec = 250

TXN_FEES = {
    NYM: 1,
    XFER_PUBLIC: 1
}


@pytest.fixture
def addresses(helpers):
    return helpers.wallet.create_new_addresses(5)


def test_valid_txn_with_fees(helpers, mint_tokens, fees_set,
                             nodeSetWithIntegratedTokenPlugin, looper,
                             address_main, addresses, tdir, tconf):
    seq_no = get_seq_no(mint_tokens)
    remaining = 1000
    last_node = nodeSetWithIntegratedTokenPlugin[-1]
    last_node.stop()
    looper.removeProdable(last_node)
    token_req_handler = last_node.get_req_handler(TOKEN_LEDGER_ID)
    token_req_handler.utxo_cache._store.close()

    nodeSetWithIntegratedTokenPlugin = nodeSetWithIntegratedTokenPlugin[:-1]

    for address in addresses:
        inputs = [
            {ADDRESS: address_main, SEQNO: seq_no},
        ]
        outputs = [
            {ADDRESS: address, AMOUNT: 1},
            {ADDRESS: address_main, AMOUNT: remaining - 2}, # XFER fee is 1
        ]
        request = helpers.request.transfer(inputs, outputs)
        response = helpers.sdk.send_and_check_request_objects([request])
        result = helpers.sdk.get_first_result(response)
        seq_no = get_seq_no(result)
        remaining -= 2

    for _ in range(5):
        pay_fees(helpers, fees_set, address_main, mint_tokens)

    config_helper = PNodeConfigHelper(last_node.name, tconf, chroot=tdir)
    restarted_node = TestNode(last_node.name,
                              config_helper=config_helper,
                              config=tconf, ha=last_node.nodestack.ha,
                              cliha=last_node.clientstack.ha)

    integrate_token_plugin_in_node(restarted_node)
    integrate_fees_plugin_in_node(restarted_node)

    tl = restarted_node.getLedger(TOKEN_LEDGER_ID)
    for node in nodeSetWithIntegratedTokenPlugin:
        token_ledger = node.getLedger(TOKEN_LEDGER_ID)
        assert token_ledger.size > tl.size

    looper.add(restarted_node)
    nodeSetWithIntegratedTokenPlugin.append(restarted_node)

    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)
