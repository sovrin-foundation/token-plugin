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


class UTXOFeeHandler(WriteRequestHandler):

    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, None, None)

    def static_validation(self, request: Request):
        pass

    def dynamic_validation(self, request: Request):
        pass

    def update_state(self, txn, prev_result, request, is_committed=False):
        # prev_result must be txns from domain_fee_handler
        txns = prev_result
        for txn in txns:
            self.update_utxo_cache(txn, is_committed=is_committed)

    def update_utxo_cache(self, txn, is_committed=False):
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
