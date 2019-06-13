import pytest
from sovtoken.constants import ADDRESS, AMOUNT, OUTPUTS, SEQNO

from indy_common.constants import NYM
from sovtokenfees.test.constants import NYM_FEES_ALIAS
from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_nym_with_fees, send_and_check_transfer, \
    ensure_all_nodes_have_same_data

from plenum.common.txn_util import get_seq_no

from plenum.common.exceptions import RequestRejectedException

from plenum.test.helper import sdk_get_and_check_replies

from indy_node.test.pool_config.helper import sdk_pool_config_sent

TXN_IN_BATCH = 2


@pytest.fixture(scope="module")
def tconf(tconf):
    old_max_size = tconf.Max3PCBatchSize
    old_time = tconf.Max3PCBatchWait
    tconf.Max3PCBatchSize = TXN_IN_BATCH
    tconf.Max3PCBatchWait = 150
    yield tconf

    tconf.Max3PCBatchSize = old_max_size
    tconf.Max3PCBatchWait = old_time


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    helpers.general.do_mint(outputs, no_wait=True)
    return helpers.general.do_mint(outputs)


def test_chain_set_fees_and_nym_batch_size_2(looper, helpers,
                                             nodeSetWithIntegratedTokenPlugin,
                                             sdk_pool_handle, sdk_wallet_trustee,
                                             mint_tokens, addresses, poolConfigWTFF):
    """
    Set FEES for NYM with cost 2

    Send any transaction to config ledger.

    Send NYM with fees 2 from A

    Set FEES for NYM with cost 3

    Send any transaction to config ledger.

    Send NYM with fees 3 from A

    Check that first NYM is not written and second NYM is.
    """
    A, B = addresses
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = get_seq_no(mint_tokens)

    # Set fees and some config txn
    fees_nym_2 = {NYM_FEES_ALIAS: 2}
    fees_2_resp = helpers.general.set_fees_without_waiting(fees_nym_2)
    sdk_pool_config_sent(looper, sdk_pool_handle,
                         sdk_wallet_trustee, poolConfigWTFF)
    sdk_get_and_check_replies(looper, fees_2_resp)

    # NYM with fees 2 from A
    _, _, b_2_nym = send_and_check_nym_with_fees(helpers,
                                                 {'fees': fees_nym_2},
                                                 seq_no,
                                                 looper,
                                                 [A],
                                                 current_amount,
                                                 check_reply=False)
    # Set fees for NYM to 3
    fees_nym_3 = {NYM_FEES_ALIAS: 3}
    fees_3_resp = helpers.general.set_fees_without_waiting(fees_nym_3)
    sdk_pool_config_sent(looper, sdk_pool_handle,
                         sdk_wallet_trustee, poolConfigWTFF)
    sdk_get_and_check_replies(looper, fees_3_resp)

    # Send NYM with fees 3
    current_amount, seq_no, b_3_nym = send_and_check_nym_with_fees(helpers,
                                                                   {'fees': fees_nym_3},
                                                                   seq_no,
                                                                   looper,
                                                                   [A],
                                                                   current_amount,
                                                                   check_reply=False)

    with pytest.raises(RequestRejectedException):
        sdk_get_and_check_replies(looper, b_2_nym)
    sdk_get_and_check_replies(looper, b_3_nym)
    a_get = helpers.general.do_get_utxo(A)
    assert a_get[OUTPUTS][1][AMOUNT] == current_amount
    assert a_get[OUTPUTS][1][SEQNO] == seq_no

    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)
