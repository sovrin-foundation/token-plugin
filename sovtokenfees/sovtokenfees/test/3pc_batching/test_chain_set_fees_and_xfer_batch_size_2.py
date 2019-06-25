import pytest
from sovtoken.constants import ADDRESS, AMOUNT, OUTPUTS, SEQNO

from indy_common.constants import NYM, CONFIG_LEDGER_ID
from sovtokenfees import FeesTransactions
from sovtokenfees.req_handlers.read_handlers.get_fees_handler import GetFeesHandler
from sovtokenfees.test.constants import XFER_PUBLIC_FEES_ALIAS
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


def test_chain_set_fees_and_xfer_batch_size_2(looper, helpers,
                                              nodeSetWithIntegratedTokenPlugin,
                                              sdk_pool_handle, sdk_wallet_trustee,
                                              mint_tokens, addresses, poolConfigWTFF):
    """
    Set FEES for XFER for 2

    Send any transaction to config ledger.

    Send XFER with fees 2 from A to B

    Set FEES for XFER for 3

    Send any transaction to config ledger.

    Send XFER with fees 3 from A to B

    Check that first XFER is not written and second XFER is.
    """
    A, B = addresses
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = get_seq_no(mint_tokens)
    transfer_summ = 20

    # Set fees and some config txn
    helpers.node.set_fees_directly({XFER_PUBLIC_FEES_ALIAS: 42})
    fees_xfer_2 = {XFER_PUBLIC_FEES_ALIAS: 2}
    fees_2_rsp = helpers.general.set_fees_without_waiting(fees_xfer_2)
    sdk_pool_config_sent(looper, sdk_pool_handle,
                         sdk_wallet_trustee, poolConfigWTFF)
    sdk_get_and_check_replies(looper, fees_2_rsp)

    # XFER with fees 2 from A to B
    _, _, a_b_transfer_2 = send_and_check_transfer(helpers,
                                                   [A, B],
                                                   fees_xfer_2,
                                                   looper,
                                                   current_amount,
                                                   seq_no,
                                                   transfer_summ=transfer_summ,
                                                   check_reply=False)
    # Set fees for XFER to 3
    fees_xfer_3 = {XFER_PUBLIC_FEES_ALIAS: 3}
    fees_3_rsp = helpers.general.set_fees_without_waiting(fees_xfer_3)
    sdk_pool_config_sent(looper, sdk_pool_handle,
                         sdk_wallet_trustee, poolConfigWTFF)
    sdk_get_and_check_replies(looper, fees_3_rsp)

    # Send XFER with fees from A to B
    a_amount, seq_no, a_b_transfer_3 = send_and_check_transfer(helpers,
                                                               [A, B],
                                                               fees_xfer_3,
                                                               looper,
                                                               current_amount,
                                                               seq_no,
                                                               transfer_summ=transfer_summ,
                                                               check_reply=False)
    for n in nodeSetWithIntegratedTokenPlugin:
        fee_rq = n.read_manager.request_handlers[FeesTransactions.GET_FEES.value]
        assert fee_rq
        assert fee_rq.get_fees(is_committed=True, with_proof=False) == fees_xfer_3

    with pytest.raises(RequestRejectedException):
        sdk_get_and_check_replies(looper, a_b_transfer_2)
    sdk_get_and_check_replies(looper, a_b_transfer_3)
    a_get = helpers.general.do_get_utxo(A)
    assert a_get[OUTPUTS][1][AMOUNT] == a_amount
    assert a_get[OUTPUTS][1][SEQNO] == seq_no

    b_get = helpers.general.do_get_utxo(B)
    assert b_get[OUTPUTS][0][AMOUNT] == transfer_summ
    assert b_get[OUTPUTS][0][SEQNO] == seq_no

    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)
