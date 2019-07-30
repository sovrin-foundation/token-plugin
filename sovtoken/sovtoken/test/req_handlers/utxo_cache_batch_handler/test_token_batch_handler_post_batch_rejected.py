from collections import namedtuple

from sovtoken import TOKEN_LEDGER_ID


def test_utxo_batch_handler_post_batch_rejected(utxo_batch_handler, utxo_cache):
    utxo_cache.set('1', '2')
    ThreePcBatch = namedtuple("ThreePcBatch", "state_root")
    three_ps_batch = ThreePcBatch(state_root="1")
    utxo_batch_handler.post_batch_applied(three_pc_batch=three_ps_batch)
    utxo_batch_handler.post_batch_rejected(TOKEN_LEDGER_ID)

    assert not len(utxo_cache.current_batch_ops)
    assert not len(utxo_cache.un_committed)
