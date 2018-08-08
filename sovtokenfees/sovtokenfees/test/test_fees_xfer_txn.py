import pytest

from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.common.exceptions import RequestRejectedException
from plenum.common.txn_util import get_type, get_seq_no
from sovtokenfees.constants import FEES
from sovtoken.constants import XFER_PUBLIC
from sovtoken.util import update_token_wallet_with_result
from sovtoken.test.helper import send_xfer, do_public_minting
from sovtoken.test.conftest import seller_gets


def test_xfer_with_insufficient_fees(public_minting, looper, fees_set,
                                     nodeSetWithIntegratedTokenPlugin,
                                     sdk_pool_handle,
                                     seller_token_wallet, seller_address, user1_address,
                                     user1_token_wallet):
    # Payed fees is less than required fees
    global seller_gets
    seq_no = get_seq_no(public_minting)
    fee_amount = fees_set[FEES][XFER_PUBLIC]
    user1_gets = 10
    seller_remaining = seller_gets - (user1_gets + fee_amount - 1)
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    outputs = [[user1_address, user1_gets], [seller_address, seller_remaining]]
    with pytest.raises(RequestRejectedException):
        send_xfer(looper, inputs, outputs, sdk_pool_handle)


@pytest.fixture(scope="module")
def xfer_with_fees_done(public_minting, looper, fees_set,
                   sdk_pool_handle,
                   seller_token_wallet, seller_address, user1_address,
                   user1_token_wallet):
    global seller_gets
    seq_no = get_seq_no(public_minting)
    fee_amount = fees_set[FEES][XFER_PUBLIC]
    user1_gets = 10
    seller_remaining = seller_gets - (user1_gets + fee_amount)
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    outputs = [[user1_address, user1_gets], [seller_address, seller_remaining]]
    res = send_xfer(looper, inputs, outputs, sdk_pool_handle)
    update_token_wallet_with_result(seller_token_wallet, res)
    update_token_wallet_with_result(user1_token_wallet, res)
    return seller_remaining, user1_gets, res


def test_xfer_with_sufficient_fees(xfer_with_fees_done, looper, fees_set,
                   nodeSetWithIntegratedTokenPlugin, sdk_pool_handle,
                   seller_token_wallet, seller_address, user1_address,
                   user1_token_wallet):
    global seller_gets
    seller_remaining, user1_gets, res = xfer_with_fees_done
    fee_amount = fees_set[FEES][XFER_PUBLIC]
    assert seller_remaining == seller_token_wallet.get_total_address_amount(seller_address)
    assert user1_gets == user1_token_wallet.get_total_address_amount(user1_address)
    seller_gets = seller_remaining
    for node in nodeSetWithIntegratedTokenPlugin:
        req_handler = node.get_req_handler(CONFIG_LEDGER_ID)
        assert req_handler.deducted_fees["{}#{}".format(get_type(res), get_seq_no(res))] == fee_amount


def test_mint_after_paying_fees(xfer_with_fees_done, looper, nodeSetWithIntegratedTokenPlugin,
                             trustee_wallets, SF_address, seller_address,
                             sdk_pool_handle):
    # Try another minting after doing some txns with fees
    total_mint = 100
    sf_master_gets = 60
    do_public_minting(looper, trustee_wallets, sdk_pool_handle, total_mint,
                      sf_master_gets, SF_address, seller_address)
