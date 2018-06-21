import pytest

from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.common.exceptions import RequestRejectedException
from plenum.common.txn_util import get_seq_no
from plenum.server.plugin.sovtoken_fees.src.constants import FEES
from plenum.server.plugin.sovtoken.src.constants import XFER_PUBLIC
from plenum.server.plugin.sovtoken.src.util import update_token_wallet_with_result
from plenum.server.plugin.sovtoken.test.helper import send_xfer
from plenum.server.plugin.sovtoken.test.conftest import seller_gets
from plenum.server.plugin.sovtoken_fees.test.test_set_get_fees import fees_set


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


def test_xfer_with_sufficient_fees(public_minting, looper, fees_set,
                   nodeSetWithIntegratedTokenPlugin, sdk_pool_handle,
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
    assert seller_remaining == seller_token_wallet.get_total_address_amount(seller_address)
    assert user1_gets == user1_token_wallet.get_total_address_amount(user1_address)
    seller_gets = seller_remaining
    for node in nodeSetWithIntegratedTokenPlugin:
        req_handler = node.get_req_handler(CONFIG_LEDGER_ID)
        assert req_handler.deducted_fees[get_seq_no(res)] == fee_amount
