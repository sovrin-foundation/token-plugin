from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import UTXO_CACHE_LABEL
from sovtoken.request_handlers.token_utils import commit_to_utxo_cache
from sovtokenfees.constants import FEES
from sovtokenfees.req_handlers.fees_utils import BatchFeesTracker

from common.serializers.serialization import txn_root_serializer
from plenum.common.constants import DOMAIN_LEDGER_ID
from plenum.common.txn_util import get_seq_no, get_type
from plenum.server.batch_handlers.batch_request_handler import BatchRequestHandler
from plenum.server.batch_handlers.three_pc_batch import ThreePcBatch
from stp_core.common.log import getlogger

logger = getlogger()


class DomainFeeBatchHandler(BatchRequestHandler):
    def __init__(self, database_manager, fees_tracker: BatchFeesTracker, token_tracker):
        super().__init__(database_manager, DOMAIN_LEDGER_ID)
        self._fees_tracker = fees_tracker
        self._token_tracker = token_tracker

    @property
    def token_state(self):
        return self.database_manager.get_state(TOKEN_LEDGER_ID)

    @property
    def token_ledger(self):
        return self.database_manager.get_ledger(TOKEN_LEDGER_ID)

    @property
    def utxo_cache(self):
        return self.database_manager.get_store(UTXO_CACHE_LABEL)

    def post_batch_applied(self, three_pc_batch, prev_handler_result=None):
        self._token_tracker.apply_batch(self.token_state.headHash,
                                        self.token_ledger.uncommitted_root_hash,
                                        self.token_ledger.uncommitted_size)
        if self._fees_tracker.fees_in_current_batch > 0:
            state_root = self.token_state.headHash
            self.utxo_cache.create_batch_from_current(state_root)
            self._fees_tracker.fees_in_current_batch = 0

    def post_batch_rejected(self, ledger_id, prev_handler_result=None):
        uncommitted_hash, uncommitted_txn_root, txn_count = self._token_tracker.reject_batch()
        if txn_count == 0 or self.token_ledger.uncommitted_root_hash == uncommitted_txn_root or \
                self.token_state.headHash == uncommitted_hash:
            return 0
        self.token_state.revertToHead(uncommitted_hash)
        self.token_ledger.discardTxns(txn_count)
        count_reverted = self.utxo_cache.reject_batch()
        logger.info("Reverted {} txns with fees".format(count_reverted))

    def commit_batch(self, three_pc_batch, prev_handler_result=None):
        committed_txns = prev_handler_result
        token_state_root, token_txn_root, _ = self._token_tracker.commit_batch()
        committed_seq_nos_with_fees = [get_seq_no(t) for t in committed_txns
                                       if self._fees_tracker.has_deducted_fees(get_type(t), get_seq_no(t))]
        if len(committed_seq_nos_with_fees) > 0:
            # This is a fake txn only for commit to token ledger
            token_fake_three_pc_batch = ThreePcBatch(ledger_id=TOKEN_LEDGER_ID,
                                                     inst_id=three_pc_batch.inst_id,
                                                     view_no=three_pc_batch.view_no,
                                                     pp_seq_no=three_pc_batch.pp_seq_no,
                                                     pp_time=three_pc_batch.pp_time,
                                                     state_root=token_state_root,
                                                     txn_root=txn_root_serializer.serialize(token_txn_root),
                                                     primaries=three_pc_batch.primaries,
                                                     valid_digests=[i for i in range(len(committed_seq_nos_with_fees))])
            committed_token_txns = super()._commit(self.token_ledger, self.token_state, token_fake_three_pc_batch)
            commit_to_utxo_cache(self.utxo_cache, token_state_root)
            i = 0
            # We are adding fees txn to the reply, so that client could get information about token transition
            for txn in committed_txns:
                if get_seq_no(txn) in committed_seq_nos_with_fees:
                    txn[FEES] = committed_token_txns[i]
                    i += 1
            self._fees_tracker.fees_in_current_batch = 0
        return committed_txns
