def test_xfer_handler_update_state(xfer_handler, xfer_txn, payment_address_2):
    xfer_handler.update_state(xfer_txn, None)

    token_state = xfer_handler.state
    utxo_cache = xfer_handler._utxo_cache

    assert int(token_state.get((payment_address_2[8:] + ":2").encode(), isCommitted=False)) == 10
    assert utxo_cache.get(payment_address_2[8:]) == '2:10'
