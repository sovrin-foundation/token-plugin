from sovtoken.constants import UTXO_CACHE_LABEL, TOKEN_LEDGER_ID

from plenum.common.constants import NYM, TXN_METADATA_SEQ_NO, TXN_METADATA, TXN_PAYLOAD, TXN_PAYLOAD_TYPE
from plenum.server.batch_handlers.three_pc_batch import ThreePcBatch


def test_fee_batch_handler_commit_batch(fee_batch_handler, fees_tracker):
    utxo_cache = fee_batch_handler.database_manager.get_store(UTXO_CACHE_LABEL)
    utxo_cache.set('1', '2')
    fee_batch_handler.database_manager.get_state(TOKEN_LEDGER_ID).set('1'.encode(), '2'.encode())
    fees_tracker.fees_in_current_batch = 1
    fee_batch_handler.post_batch_applied(None, None)

    fees_tracker.add_deducted_fees(NYM, 1, 1)
    prev_res = [{
        TXN_METADATA: {
            TXN_METADATA_SEQ_NO: 1
        },
        TXN_PAYLOAD: {
            TXN_PAYLOAD_TYPE: NYM
        }
    }]

    three_pc_batch = ThreePcBatch(0, 0, 0, 3, 1, 'state', 'txn',
                                  ['a', 'b', 'c'], ['a'], 0)

    fee_batch_handler.commit_batch(three_pc_batch, prev_res)
    assert not len(utxo_cache.current_batch_ops)
    assert not len(utxo_cache.un_committed)
    assert fee_batch_handler.token_ledger.committed_root_hash == fee_batch_handler.token_ledger.uncommitted_root_hash
    assert fee_batch_handler.token_state.headHash == fee_batch_handler.token_state.committedHeadHash
