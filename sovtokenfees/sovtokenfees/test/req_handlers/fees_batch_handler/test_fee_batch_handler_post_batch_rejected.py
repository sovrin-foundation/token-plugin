from sovtoken.constants import UTXO_CACHE_LABEL, TOKEN_LEDGER_ID


def test_fee_batch_handler_post_batch_rejected(fee_batch_handler, fees_tracker):
    utxo_cache = fee_batch_handler.database_manager.get_store(UTXO_CACHE_LABEL)
    utxo_cache.set('1', '2')
    fee_batch_handler.database_manager.get_state(TOKEN_LEDGER_ID).set('1'.encode(), '2'.encode())
    fees_tracker.fees_in_current_batch = 1
    fee_batch_handler.post_batch_applied(None, None)
    fee_batch_handler.post_batch_rejected(None, None)
    assert not len(utxo_cache.current_batch_ops)
    assert not len(utxo_cache.un_committed)
    assert not len(fee_batch_handler.token_tracker.un_committed)
