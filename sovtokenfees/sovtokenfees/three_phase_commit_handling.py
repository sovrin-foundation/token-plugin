from plenum.common.types import f
from plenum.common.util import updateNamedTuple
from sovtokenfees.constants import FEES, FEE_TXNS_IN_BATCH
from sovtoken import TOKEN_LEDGER_ID


class ThreePhaseCommitHandler:
    def __init__(self, master_replica, token_ledger, token_state,
                 fees_req_handler):
        self.master_replica = master_replica
        self.token_ledger = token_ledger
        self.token_state = token_state
        self.fees_req_handler = fees_req_handler

    # adds a pre_prepare message to be sent that includes the fee transaction info in
    # the "plugins_fields" member
    def add_to_pre_prepare(self, pre_prepare):
        if pre_prepare.ledgerId != TOKEN_LEDGER_ID and \
                self.fees_req_handler.fee_txns_in_current_batch > 0:
            # Make sovtoken ledger and state root part of pre-prepare
            extra = {
                f.PLUGIN_FIELDS.nm: {
                    FEES: {
                        FEE_TXNS_IN_BATCH: self.fees_req_handler.fee_txns_in_current_batch,
                        f.STATE_ROOT.nm: self.master_replica.stateRootHash(
                            TOKEN_LEDGER_ID),
                        f.TXN_ROOT.nm: self.master_replica.txnRootHash(
                            TOKEN_LEDGER_ID)
                    }
                }
            }
            pre_prepare = updateNamedTuple(pre_prepare, **extra)
        return pre_prepare

    # adds a prepare message to be sent that includes the fee transaction info in
    # the "plugins_fields" member
    def add_to_prepare(self, prepare, pre_prepare):
        if pre_prepare.ledgerId != TOKEN_LEDGER_ID and \
                self._has_plugin_fields(pre_prepare):
            # Make sovtoken ledger and state root part of pre-prepare
            pre_prepare_fees_data = pre_prepare.plugin_fields.get(FEES, {})
            if pre_prepare_fees_data:
                extra = {
                    f.PLUGIN_FIELDS.nm: {
                        FEES: {
                            FEE_TXNS_IN_BATCH: pre_prepare_fees_data.get(
                                FEE_TXNS_IN_BATCH),
                            f.STATE_ROOT.nm: pre_prepare_fees_data.get(
                                f.STATE_ROOT.nm),
                            f.TXN_ROOT.nm: pre_prepare_fees_data.get(f.TXN_ROOT.nm)
                        }
                    }
                }
                prepare = updateNamedTuple(prepare, **extra)
        return prepare

    def add_to_commit(self, commit):
        # Nothing needed in commit
        return commit

    # ?
    def add_to_ordered(self, ordered, pre_prepare):
        if pre_prepare.ledgerId != TOKEN_LEDGER_ID and \
                self._has_plugin_fields(pre_prepare):
            pre_prepare_fees_data = pre_prepare.plugin_fields.get(FEES, {})
            if pre_prepare_fees_data:
                # the plugins_fields member created here is an exact copy of the one found in the pre_prepare msg
                extra = {
                    f.PLUGIN_FIELDS.nm: {
                        FEES: {
                            FEE_TXNS_IN_BATCH: pre_prepare_fees_data.get(
                                FEE_TXNS_IN_BATCH),
                            f.STATE_ROOT.nm: pre_prepare_fees_data.get(
                                f.STATE_ROOT.nm),
                            f.TXN_ROOT.nm: pre_prepare_fees_data.get(f.TXN_ROOT.nm)
                        }
                    }
                }
                ordered = updateNamedTuple(ordered, **extra)
        return ordered

    # Checks to make sure the pre_prepare message was properly appended and formatted with fee info
    def check_recvd_pre_prepare(self, pre_prepare):
        if pre_prepare.ledgerId != TOKEN_LEDGER_ID:
            fee_txn_count = self.fees_req_handler.fee_txns_in_current_batch
            if fee_txn_count > 0:
                if not self._has_plugin_fields(pre_prepare):
                    raise Exception('Expected {} in PRE-PREPARE'.format(f.PLUGIN_FIELDS.nm))

                fees = pre_prepare.plugin_fields.get(FEES)
                if not fees:
                    raise Exception('Expected {} in PRE-PREPARE'.format(FEES))

                if fees.get(FEE_TXNS_IN_BATCH) != fee_txn_count:
                    raise Exception('{} mismatch in PRE-PREPARE '
                                    'expected {}, found {}'.format(
                                                                FEE_TXNS_IN_BATCH,
                                                                fee_txn_count,
                                                                fees.get(FEE_TXNS_IN_BATCH)))

                recvd_state_root = self.master_replica._state_root_serializer.deserialize(
                        fees.get(f.STATE_ROOT.nm, '').encode())
                if recvd_state_root != self.fees_req_handler.token_state.headHash:
                    raise Exception('{} mismatch in PRE-PREPARE '
                                    'expected {}, found {}'.format(
                                                                f.STATE_ROOT.nm,
                                                                self.fees_req_handler.token_state.headHash,
                                                                recvd_state_root))

                recvd_txn_root = self.token_ledger.strToHash(fees.get(f.TXN_ROOT.nm, ''))
                if recvd_txn_root != self.fees_req_handler.token_ledger.uncommittedRootHash:
                    raise Exception('{} mismatch in PRE-PREPARE '
                                    'expected {}, found {}'.format(
                                                                f.TXN_ROOT.nm,
                                                                self.fees_req_handler.token_ledger.uncommittedRootHash,
                                                                recvd_txn_root))

    # Checks to make sure the prepare message was properly appended and formatted with fee info
    def check_recvd_prepare(self, prepare, pre_prepare):
        # TODO:
        return

    # Checks to make sure the commit message was properly appended and formatted with fee info
    def check_recvd_commit(self, commit):
        # No check needed in commit
        return

    # ?
    def batch_created(self, ledger_id, state_root):
        # Need old state root hash to preserve
        pass

    # ?
    def batch_rejected(self, ledger_id):
        pass

    # Makes sure that the "plugins_fields" member is contained in a message. This field is what distinguishes normal
    # messages from messages that support the sovrin plugin
    @staticmethod
    def _has_plugin_fields(msg):
        try:
            getattr(msg, f.PLUGIN_FIELDS.nm)
            return True
        except (AttributeError, KeyError):
            return False
