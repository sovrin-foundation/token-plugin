import pytest

from plenum.test.helper import checkViewNoForNodes, waitForViewChange, sdk_send_random_and_check
from plenum.test.node_catchup.helper import ensure_all_nodes_have_same_data
from plenum.test.node_request.helper import sdk_ensure_pool_functional
from plenum.test.test_node import ensureElectionsDone
from sovtoken.constants import ADDRESS, AMOUNT
from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no
from sovtokenfees.constants import FEES
from sovtokenfees.test.catchup.helper import scenario_txns_during_catchup
from sovtokenfees.test.constants import NYM_FEES_ALIAS, NODE_FEES_ALIAS, XFER_PUBLIC_FEES_ALIAS, alias_to_txn_type
from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_nym_with_fees, send_and_check_transfer, \
    add_fees_request_with_address

from plenum.test.pool_transactions.helper import prepare_node_request, disconnect_node_and_ensure_disconnected

from plenum.common.util import hexToFriendly
from sovtokenfees.test.helpers import HelperNode

from indy_node.test.helper import start_stopped_node

from plenum.common.constants import KeyValueStorageType

nodeCount = 6  # noqa: N816

whitelist = ['Consistency verification of merkle tree from hash store failed']


@pytest.fixture(scope="module")
def tconf(tconf):
    old_b_size = tconf.Max3PCBatchSize
    tconf.Max3PCBatchSize = 1

    yield tconf
    tconf.Max3PCBatchSize = old_b_size


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


@pytest.fixture(
    scope='module',
    params=[
        {NYM_FEES_ALIAS: 4,
         XFER_PUBLIC_FEES_ALIAS: 4},  # with fees
    ], ids=lambda x: 'fees'
)
def fees(request):
    return request.param


def demote_node(helpers, wallet, node):
    req = helpers.sdk.sdk_build_demote_txn(node, wallet)
    helpers.sdk.send_request_objects([req], wallet)


def promote_node(helpers, wallet, node):
    req = helpers.sdk.sdk_build_promote_txn(node, wallet)
    helpers.sdk.send_request_objects([req], wallet)


def restart_node(restarted_node, pool, looper, tconf, tdir, allPluginsPath, do_post_node_creation, fees):
    node_idx = pool.index(restarted_node)
    restarted_node.cleanupOnStopping = False
    disconnect_node_and_ensure_disconnected(looper,
                                            pool,
                                            restarted_node.name,
                                            stopNode=True)
    looper.removeProdable(name=restarted_node.name)
    restarted_node = start_stopped_node(
        restarted_node,
        looper,
        tconf,
        tdir,
        allPluginsPath,
        start=False,
    )
    do_post_node_creation(restarted_node)
    for fee_alias, amount in fees.items():
        HelperNode.fill_auth_map_for_node(restarted_node, alias_to_txn_type[fee_alias])
    pool[node_idx] = restarted_node
    looper.add(restarted_node)


def test_demote_promote_restart_after_promotion(nodeSetWithIntegratedTokenPlugin,
                                                looper,
                                                sdk_pool_handle,
                                                sdk_wallet_trustee,
                                                tdir,
                                                tconf,
                                                allPluginsPath,
                                                mint_tokens,
                                                address_main,
                                                helpers,
                                                fees_set, addresses, fees,
                                                do_post_node_creation):
    pool = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = 1
    demoted_node = pool[-1]

    from_a_to_b = [addresses[0], addresses[1]]
    current_amount, seq_no, _ = send_and_check_transfer(helpers, from_a_to_b, fees, looper,
                                                        current_amount, seq_no)

    rest_nodes = [n for n in pool if n != demoted_node]

    starting_view_no = checkViewNoForNodes(pool)

    # Step 1. Demote for node Zeta

    demote_node(helpers, sdk_wallet_trustee, demoted_node)

    # Step 2. Waiting for view change after nodes count changing
    waitForViewChange(looper, rest_nodes, expectedViewNo=starting_view_no + 1)
    ensureElectionsDone(looper, rest_nodes)
    ensure_all_nodes_have_same_data(looper, rest_nodes, exclude_from_check='check_seqno_db_equality')

    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount)

    current_amount, seq_no, _ = send_and_check_transfer(helpers, from_a_to_b, fees, looper,
                                                        current_amount, seq_no)

    starting_view_no = checkViewNoForNodes(rest_nodes)

    # Step 3. Promote node back and waiting for view change

    promote_node(helpers, sdk_wallet_trustee, demoted_node)

    waitForViewChange(looper, rest_nodes, expectedViewNo=starting_view_no + 1)
    ensureElectionsDone(looper, rest_nodes)

    # Step 4. Restart promoted node only after Node txn ordering

    restart_node(demoted_node, pool, looper, tconf, tdir, allPluginsPath, do_post_node_creation, fees)

    ensure_all_nodes_have_same_data(looper, pool, custom_timeout=60, exclude_from_check='check_seqno_db_equality')
    ensureElectionsDone(looper, pool)

    # Step 5. Make sure that pool works fine

    current_amount, seq_no, _ = send_and_check_transfer(helpers, from_a_to_b, fees, looper,
                                                        current_amount, seq_no)
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses,
                                                             current_amount)
    ensure_all_nodes_have_same_data(looper, pool, exclude_from_check='check_seqno_db_equality')
    # sdk_ensure_pool_functional(looper, pool, sdk_wallet_steward, sdk_pool_handle)
