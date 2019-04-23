import pytest
from sovtoken.constants import ADDRESS, AMOUNT, OUTPUTS

from indy_common.constants import NYM
from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_nym_with_fees, send_and_check_transfer, \
    ensure_all_nodes_have_same_data

from plenum.common.txn_util import get_seq_no, get_payload_data

from plenum.common.exceptions import RequestRejectedException

from plenum.test.helper import sdk_get_and_check_replies

from plenum.test import waits

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
    return helpers.wallet.create_new_addresses(3)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    helpers.general.do_mint(outputs, no_wait=True)
    return helpers.general.do_mint(outputs)


@pytest.fixture()
def fees():
    return {NYM: 4}


@pytest.fixture()
def fees_set(helpers, fees):
    fees2 = {NYM: 2}
    fees4 = fees
    helpers.general.set_fees_without_waiting(fees2)
    helpers.general.set_fees_without_waiting(fees4)
    return {'fees': fees4}


def test_chain_fees_and_xfer_batch_size_2(looper, helpers,
                                          nodeSetWithIntegratedTokenPlugin,
                                          fees_set, mint_tokens, addresses, fees):
    """
    Set FEES for NYM transaction

    Send XFER from A to B

    Send NYM with fees from A using the UTXO as in 2

    Send XFER from B to C

    Send NYM with fees from C

    Check that XFERs are written

    Check that first NYM is not written and the second one is written.
    """
    a_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = get_seq_no(mint_tokens)
    initial_seq_no = seq_no
    A, B, C = addresses

    transfer_summ = 20
    # From A to B transfer
    a_amount, seq_no, a_b_transfer = send_and_check_transfer(helpers,
                                                             [A, B],
                                                             fees,
                                                             looper,
                                                             a_amount,
                                                             seq_no,
                                                             transfer_summ=transfer_summ,
                                                             check_reply=False)
    # NYM with fees from A and utxo as for previous case
    _, _, a_nym = send_and_check_nym_with_fees(helpers,
                                               fees_set,
                                               initial_seq_no,
                                               looper,
                                               [A],
                                               a_amount + transfer_summ,
                                               check_reply=False)
    # From B to C transfer
    b_amount, seq_no, b_c_transfer = send_and_check_transfer(helpers,
                                                             [B, C],
                                                             fees,
                                                             looper,
                                                             transfer_summ,
                                                             seq_no,
                                                             transfer_summ=transfer_summ,
                                                             check_reply=False)
    sdk_get_and_check_replies(looper, a_b_transfer)
    sdk_get_and_check_replies(looper, b_c_transfer)
    b_c_get = helpers.general.do_get_utxo(B)
    assert len(b_c_get[OUTPUTS]) == 0

    # NYM with fees from C
    c_nym_amount, seq_no, c_nym = send_and_check_nym_with_fees(helpers,
                                                               fees_set,
                                                               seq_no,
                                                               looper,
                                                               [C],
                                                               transfer_summ,
                                                               check_reply=False)
    with pytest.raises(RequestRejectedException, match="are not found in list of"):
        sdk_get_and_check_replies(looper, a_nym)
    a_b_get = helpers.general.do_get_utxo(A)
    assert a_b_get[OUTPUTS][1][AMOUNT] == a_amount

    sdk_get_and_check_replies(looper, c_nym)
    c_nym_get = helpers.general.do_get_utxo(C)
    assert c_nym_get[OUTPUTS][0][AMOUNT] == c_nym_amount == transfer_summ - fees.get(NYM, 0)

    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)

