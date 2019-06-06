import base58
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.exceptions import TokenValueError

from plenum.server.batch_handlers.batch_request_handler import BatchRequestHandler
from plenum.server.database_manager import DatabaseManager


class TokenBatchHandler(BatchRequestHandler):

    def __init__(self, database_manager: DatabaseManager):
        super().__init__(database_manager, TOKEN_LEDGER_ID)

    def post_batch_rejected(self, ledger_id, prev_handler_result=None):
        self.database_manager.get_store("utxo_cache").reject_batch()

    def post_batch_applied(self, three_pc_batch, prev_handler_result=None):
        self.database_manager.get_store("utxo_cache").create_batch_from_current(three_pc_batch.state_root)

    def commit_batch(self, three_pc_batch, prev_handler_result=None):
        super().commit_batch(three_pc_batch, prev_handler_result)
        state_root = base58.b58decode(three_pc_batch.state_root.encode()) if isinstance(
            three_pc_batch.state_root, str) else three_pc_batch.state_root
        if self.database_manager.get_store("utxo_cache").first_batch_idr != state_root:
            raise TokenValueError(
                'state_root', state_root,
                ("equal to utxo_cache.first_batch_idr hash {}"
                 .format(self.database_manager.get_store("utxo_cache").first_batch_idr))
            )
        self.database_manager.get_store("utxo_cache").commit_batch()

