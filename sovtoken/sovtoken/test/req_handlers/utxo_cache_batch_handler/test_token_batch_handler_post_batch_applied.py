from collections import namedtuple


def test_utxo_batch_handler_post_batch_applied(utxo_batch_handler, utxo_cache):
    utxo_cache.set('1', '2')
    ThreePcBatch = namedtuple("ThreePcBatch", "state_root")
    three_ps_batch = ThreePcBatch(state_root="1")
    utxo_batch_handler.post_batch_applied(three_pc_batch=three_ps_batch)

    assert not len(utxo_cache.current_batch_ops)
    assert len(utxo_cache.un_committed) == 1
    assert utxo_cache.un_committed[0] == ('1', {'1': '2'})
