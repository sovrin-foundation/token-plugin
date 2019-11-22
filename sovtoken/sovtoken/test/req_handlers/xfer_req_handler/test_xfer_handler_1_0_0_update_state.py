from sovtoken.test.helper import libsovtoken_address_to_address


def test_xfer_handler_update_state(xfer_handler_1_0_0, xfer_txn, payment_address, payment_address_2):
    xfer_handler_1_0_0.update_state(xfer_txn, None, None)

    token_state = xfer_handler_1_0_0.state
    utxo_cache = xfer_handler_1_0_0.utxo_cache

    assert int(
        token_state.get((libsovtoken_address_to_address(payment_address_2) + ":2").encode(), isCommitted=False)) == 10
    assert utxo_cache.get(libsovtoken_address_to_address(payment_address_2)) == '2:10'
    assert token_state.get((libsovtoken_address_to_address(payment_address) + ":1").encode(), isCommitted=False) == b''
