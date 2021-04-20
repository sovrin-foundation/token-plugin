from sovtoken import TOKEN_LEDGER_ID

from plenum.server.batch_handlers.batch_request_handler import BatchRequestHandler


class TrackerBatchHandler(BatchRequestHandler):
    def __init__(self, database_manager):
        super().__init__(database_manager, TOKEN_LEDGER_ID)

    @property
    def token_state(self):
        return self.database_manager.get_state(TOKEN_LEDGER_ID)

    @property
    def token_ledger(self):
        return self.database_manager.get_ledger(TOKEN_LEDGER_ID)

    @property
    def token_tracker(self):
        return self.database_manager.get_tracker(TOKEN_LEDGER_ID)

    def post_batch_applied(self, three_pc_batch, prev_handler_result=None):
        self.token_tracker.apply_batch(self.token_state.headHash,
                                       self.token_ledger.uncommitted_root_hash,
                                       self.token_ledger.uncommitted_size)

    def post_batch_rejected(self, ledger_id, prev_handler_result=None):
        self.token_tracker.reject_batch()

    def commit_batch(self, three_pc_batch, prev_handler_result=None):
        self.token_tracker.commit_batch()
