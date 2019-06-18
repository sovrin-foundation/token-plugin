from sovtoken.constants import UTXO_CACHE_LABEL, TOKEN_LEDGER_ID


def test_fee_batch_handler_post_batch_applied(fee_batch_handler, fees_tracker):
    utxo_cache = fee_batch_handler.database_manager.get_store(UTXO_CACHE_LABEL)
    utxo_cache.set('1', '2')
    fees_tracker.fees_in_current_batch = 1
    fee_batch_handler.post_batch_applied(None, None)
    assert not len(utxo_cache.current_batch_ops)
    assert len(utxo_cache.un_committed) == 1
    assert utxo_cache.un_committed[0] == (fee_batch_handler.token_state.headHash, {'1': '2'})
    assert fee_batch_handler._fees_tracker.fees_in_current_batch == 0
    assert fee_batch_handler._token_tracker.un_committed[0] == (
        fee_batch_handler.token_state.headHash,
        fee_batch_handler.token_ledger.uncommitted_root_hash,
        fee_batch_handler.token_ledger.uncommitted_size
    )
