from plenum.common.types import f
from plenum.common.util import updateNamedTuple
from plenum.server.plugin.fees.src.constants import FEES, FEE_TXNS_IN_BATCH
from plenum.server.plugin.token import TOKEN_LEDGER_ID


class ThreePhaseCommitHandler:
    def __init__(self, master_replica, token_ledger, token_state,
                 fees_req_handler):
        self.master_replica = master_replica
        self.token_ledger = token_ledger
        self.token_state = token_state
        self.fees_req_handler = fees_req_handler

    def add_to_pre_prepare(self, pre_prepare):
        if pre_prepare.ledgerId != TOKEN_LEDGER_ID and \
                self.fees_req_handler.fee_txns_in_current_batch > 0:
            # Make token ledger and state root part of pre-prepare
            extra = {
                f.PLUGIN_FIELDS.nm: {
                    FEES: {
                        FEE_TXNS_IN_BATCH: self.fees_req_handler.fee_txns_in_current_batch,
                        f.STATE_ROOT.nm: self.master_replica.stateRootHash(
                            TOKEN_LEDGER_ID),
                        f.TXN_ROOT: self.master_replica.txnRootHash(
                            TOKEN_LEDGER_ID)
                    }
                }
            }
            pre_prepare = updateNamedTuple(pre_prepare, **extra)
        return pre_prepare

    def add_to_prepare(self, prepare, pre_prepare):
        if pre_prepare.ledgerId != TOKEN_LEDGER_ID and self._has_plugin_fields(pre_prepare):
            # Make token ledger and state root part of pre-prepare
            pre_prepare_fees_data = pre_prepare.plugin_fields.get(FEES, {})
            if pre_prepare_fees_data:
                extra = {
                    f.PLUGIN_FIELDS.nm: {
                        FEES: {
                            FEE_TXNS_IN_BATCH: pre_prepare_fees_data.get(
                                FEE_TXNS_IN_BATCH),
                            f.STATE_ROOT.nm: pre_prepare_fees_data.get(
                                f.STATE_ROOT.nm),
                            f.TXN_ROOT: pre_prepare_fees_data.get(f.TXN_ROOT.nm)
                        }
                    }
                }
                prepare = updateNamedTuple(prepare, **extra)
        return prepare

    def add_to_commit(self, commit):
        # Nothing needed in commit
        return commit

    def add_to_ordered(self, ordered, pre_prepare):
        if pre_prepare.ledgerId != TOKEN_LEDGER_ID and \
                self._has_plugin_fields(pre_prepare):
            pre_prepare_fees_data = pre_prepare.plugin_fields.get(FEES, {})
            if pre_prepare_fees_data:
                extra = {
                    f.PLUGIN_FIELDS.nm: {
                        FEES: {
                            FEE_TXNS_IN_BATCH: pre_prepare_fees_data.get(
                                FEE_TXNS_IN_BATCH),
                            f.STATE_ROOT.nm: pre_prepare_fees_data.get(
                                f.STATE_ROOT.nm),
                            f.TXN_ROOT: pre_prepare_fees_data.get(f.TXN_ROOT.nm)
                        }
                    }
                }
                ordered = updateNamedTuple(ordered, **extra)
        return ordered

    def check_recvd_pre_prepare(self, pre_prepare):
        # TODO:
        return

    def check_recvd_prepare(self, prepare, pre_prepare):
        # TODO:
        return

    def check_recvd_commit(self, commit):
        # No check needed in commit
        return

    def batch_created(self, ledger_id, state_root):
        # Need old state root hash to preserve
        pass

    def batch_rejected(self, ledger_id):
        pass

    @staticmethod
    def _has_plugin_fields(msg):
        try:
            getattr(msg, f.PLUGIN_FIELDS.nm)
            return True
        except (AttributeError, KeyError):
            return False
