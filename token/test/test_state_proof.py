from plenum.common.constants import STATE_PROOF
from plenum.server.plugin.token.src.util import update_token_wallet_with_result

from plenum.server.plugin.token.test.helper import send_get_utxo, send_xfer
from plenum.server.plugin.token.test.test_public_xfer_2 import user1_token_wallet, user1_address


def test_xfer_with_multiple_inputs(public_minting, looper,  # noqa
                                   sdk_pool_handle, sdk_wallet_client,
                                   seller_token_wallet, seller_address,
                                   user1_token_wallet, user1_address):
    res = send_get_utxo(looper, seller_address, sdk_wallet_client, sdk_pool_handle)
    update_token_wallet_with_result(seller_token_wallet, res)

    for _ in range(20):
        utxos = [_ for lst in
                 seller_token_wallet.get_all_wallet_utxos().values()
                 for _ in lst]
        seq_no, amount = utxos[0]
        inputs = [[seller_token_wallet, seller_address, seq_no]]
        outputs = [[user1_address, 1], [seller_address, amount-1]]
        res = send_xfer(looper, inputs, outputs, sdk_pool_handle)
        update_token_wallet_with_result(seller_token_wallet, res)
        res = send_get_utxo(looper, seller_address, sdk_wallet_client,
                            sdk_pool_handle)
        update_token_wallet_with_result(seller_token_wallet, res)
        res = send_get_utxo(looper, user1_address, sdk_wallet_client,
                            sdk_pool_handle)
        update_token_wallet_with_result(user1_token_wallet, res)

    res = send_get_utxo(looper, user1_address, sdk_wallet_client,
                        sdk_pool_handle)
    assert res[STATE_PROOF]
