import base58
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import UTXO_CACHE_LABEL
from sovtoken.exceptions import TokenValueError
from sovtoken.request_handlers.token_utils import commit_to_utxo_cache

from plenum.server.batch_handlers.batch_request_handler import BatchRequestHandler
from plenum.server.database_manager import DatabaseManager


class TokenBatchHandler(BatchRequestHandler):

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
        super().commit_batch(three_pc_batch, prev_handler_result)
        commit_to_utxo_cache(self.utxo_cache, three_pc_batch.state_root)
