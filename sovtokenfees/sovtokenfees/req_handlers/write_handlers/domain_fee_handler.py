from sovtoken.constants import INPUTS, OUTPUTS, ADDRESS, UTXO_CACHE_LABEL, SEQNO, AMOUNT, TOKEN_LEDGER_ID
from sovtoken.request_handlers.token_utils import spend_input, add_new_output
from sovtoken.types import Output
from sovtokenfees.constants import FEE_TXN, REF, FEES
from sovtokenfees.fees_authorizer import FeesAuthorizer
from sovtokenfees.req_handlers.fees_utils import BatchFeesTracker

from plenum.common.constants import TXN_TYPE, DOMAIN_LEDGER_ID, TXN_PAYLOAD, TXN_PAYLOAD_DATA
from plenum.common.request import Request
from plenum.common.txn_util import get_req_id, reqToTxn, get_seq_no, get_txn_time, get_type
from plenum.common.types import f, OPERATION
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.handler_interfaces.write_request_handler import WriteRequestHandler


class DomainFeeHandler(WriteRequestHandler):

    def __init__(self, db_manager: DatabaseManager, txn_id, fees_tracker: BatchFeesTracker):
        super().__init__(db_manager, txn_id, DOMAIN_LEDGER_ID)
        self._fees_tracker = fees_tracker

    def static_validation(self, request: Request):
        pass

    def dynamic_validation(self, request: Request):
        pass

    def update_state(self, txn, prev_result, request, is_committed=False):
        txn_type = request.operation[TXN_TYPE]
        seq_no = get_seq_no(txn)
        cons_time = get_txn_time(txn)
        if FeesAuthorizer.has_fees(request):
            inputs, outputs, signatures = getattr(request, f.FEES.nm)
            # This is correct since FEES is changed from config ledger whose
            # transactions have no fees
            fees = FeesAuthorizer.calculate_fees_from_req(self.utxo_cache, request)
            sigs = {i[ADDRESS]: s for i, s in zip(inputs, signatures)}
            txn = {
                OPERATION: {
                    TXN_TYPE: FEE_TXN,
                    INPUTS: inputs,
                    OUTPUTS: outputs,
                    REF: self._get_ref_for_txn_fees(seq_no),
                    FEES: fees,
                },
                f.SIGS.nm: sigs,
                f.REQ_ID.nm: get_req_id(txn),
                f.PROTOCOL_VERSION.nm: 2,
            }
            txn = reqToTxn(txn)
            self.token_ledger.append_txns_metadata([txn], txn_time=cons_time)
            _, txns = self.token_ledger.appendTxns([txn])
            self._fees_tracker.fees_in_current_batch += 1
            self._fees_tracker.add_deducted_fees(txn_type, seq_no, fees)
            return txns

    @property
    def utxo_cache(self):
        return self.database_manager.get_store(UTXO_CACHE_LABEL)

    @property
    def token_state(self):
        return self.database_manager.get_state(TOKEN_LEDGER_ID)

    @property
    def token_ledger(self):
        return self.database_manager.get_ledger(TOKEN_LEDGER_ID)

    def gen_state_key(self, txn):
        pass

    def _get_ref_for_txn_fees(self, seq_no):
        return '{}:{}'.format(self.ledger_id, seq_no)
