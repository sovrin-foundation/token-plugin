from sovtoken.constants import INPUTS, OUTPUTS, ADDRESS, UTXO_CACHE_LABEL, SEQNO, AMOUNT, TOKEN_LEDGER_ID
from sovtoken.request_handlers.token_utils import spend_input, add_new_output
from sovtoken.types import Output
from sovtokenfees.constants import FEE_TXN, REF, FEES
from sovtokenfees.fees_authorizer import FeesAuthorizer
from sovtokenfees.req_handlers.fees_utils import BatchFeesTracker

from plenum.common.constants import TXN_TYPE, DOMAIN_LEDGER_ID, TXN_PAYLOAD, TXN_PAYLOAD_DATA
from plenum.common.request import Request
from plenum.common.txn_util import get_req_id, reqToTxn, get_seq_no, get_txn_time
from plenum.common.types import f, OPERATION
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.handler_interfaces.write_request_handler import WriteRequestHandler


class DomainFeeHandler(WriteRequestHandler):

    def __init__(self, db_manager: DatabaseManager, fees_tracker: BatchFeesTracker):
        super().__init__(db_manager, None, DOMAIN_LEDGER_ID)
        self._fees_tracker = fees_tracker

    def static_validation(self, request: Request):
        pass

    def dynamic_validation(self, request: Request):
        pass

    def apply_request(self, request: Request, batch_ts, prev_result):
        self._validate_request_type(request)
        txn_type = request.operation[TXN_TYPE]
        seq_no = get_seq_no(prev_result)
        cons_time = get_txn_time(prev_result)
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
                f.REQ_ID.nm: get_req_id(prev_result),
                f.PROTOCOL_VERSION.nm: 2,
            }
            txn = reqToTxn(txn)
            self.token_ledger.append_txns_metadata([txn], txn_time=cons_time)
            _, txns = self.token_ledger.appendTxns([txn])
            self.update_state(txn, prev_result, request)
            self._fees_tracker.fees_in_current_batch += 1
            self._fees_tracker.add_deducted_fees(txn_type, seq_no, fees)
        return None, None, prev_result

    def update_state(self, txn, prev_result, request, is_committed=False):
        for utxo in txn[TXN_PAYLOAD][TXN_PAYLOAD_DATA][INPUTS]:
            spend_input(
                state=self.token_state,
                utxo_cache=self.utxo_cache,
                address=utxo[ADDRESS],
                seq_no=utxo[SEQNO],
                is_committed=is_committed
            )
        seq_no = get_seq_no(txn)
        for output in txn[TXN_PAYLOAD][TXN_PAYLOAD_DATA][OUTPUTS]:
            add_new_output(
                state=self.token_state,
                utxo_cache=self.utxo_cache,
                output=Output(
                    output[ADDRESS],
                    seq_no,
                    output[AMOUNT]),
                is_committed=is_committed)

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
