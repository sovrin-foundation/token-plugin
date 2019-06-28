import base58
from sovtoken.constants import UTXO_CACHE_LABEL, TOKEN_LEDGER_ID
from sovtoken.exceptions import TokenValueError

from plenum.server.database_manager import DatabaseManager

from plenum.server.batch_handlers.batch_request_handler import BatchRequestHandler


class UTXOBatchHandler(BatchRequestHandler):

    def __init__(self, database_manager: DatabaseManager):
        super().__init__(database_manager, TOKEN_LEDGER_ID)

    @property
    def utxo_cache(self):
        return self.database_manager.get_store(UTXO_CACHE_LABEL)

    def post_batch_rejected(self, ledger_id, prev_handler_result=None):
        self.utxo_cache.reject_batch()

    def post_batch_applied(self, three_pc_batch, prev_handler_result=None):
        self.utxo_cache.create_batch_from_current(three_pc_batch.state_root)

    def commit_batch(self, three_pc_batch, prev_handler_result=None):
        state_root = three_pc_batch.state_root
        state_root = base58.b58decode(state_root.encode()) if isinstance(
            state_root, str) else state_root
        if self.utxo_cache.first_batch_idr != state_root:
            raise TokenValueError(
                'state_root', state_root,
                ("equal to utxo_cache.first_batch_idr hash {}"
                    .format(self.utxo_cache.first_batch_idr))
            )
        self.utxo_cache.commit_batch()
