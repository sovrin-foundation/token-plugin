from sovtoken.test.helper import libsovtoken_address_to_address


def test_xfer_handler_update_state(xfer_handler, xfer_txn, payment_address_2):
    xfer_handler.update_state(xfer_txn, None, None)

    token_state = xfer_handler.state
    utxo_cache = xfer_handler.utxo_cache

    assert int(token_state.get((libsovtoken_address_to_address(payment_address_2) + ":2").encode(), isCommitted=False)) == 10
    assert utxo_cache.get(libsovtoken_address_to_address(payment_address_2)) == '2:10'
