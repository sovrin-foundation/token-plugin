
def test_mint_handler_update_state_valid_txn(mint_txn, mint_handler, payment_address):
    mint_handler.update_state(mint_txn, None, is_committed=True)

    token_state = mint_handler.state
    utxo_cache = mint_handler.database_manager.get_store("utxo_cache")

    assert int(token_state.get((payment_address[8:] + ":1").encode(), isCommitted=False)) == 10
    assert utxo_cache.get(payment_address[8:].encode()).decode() == '1:10'


