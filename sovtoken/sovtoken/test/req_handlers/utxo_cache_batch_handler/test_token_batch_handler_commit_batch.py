from collections import namedtuple
from base58 import b58decode
from sovtokenfees.serializers import txn_root_serializer


def test_token_batch_handler_commit_batch(utxo_batch_handler, utxo_cache):
    utxo_cache.set('1', '2')
    ThreePcBatch = namedtuple("ThreePcBatch", "state_root valid_digests txn_root")
    three_ps_batch = ThreePcBatch(state_root=b58decode("1".encode()), valid_digests=["1"],
                                  txn_root=txn_root_serializer.serialize("1"))
    utxo_batch_handler.post_batch_applied(three_pc_batch=three_ps_batch)
    utxo_batch_handler.commit_batch(three_ps_batch, None)

    assert not len(utxo_cache.current_batch_ops)
    assert not len(utxo_cache.un_committed)
