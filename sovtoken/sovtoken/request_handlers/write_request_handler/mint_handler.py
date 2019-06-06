from sovtoken import TokenTransactions
from sovtoken.constants import MINT_PUBLIC, OUTPUTS, TOKEN_LEDGER_ID
from sovtoken.exceptions import UTXOError
from sovtoken.messages.txn_validator import txn_mint_public_validate
from sovtoken.request_handlers.token_utils import add_new_output
from sovtoken.types import Output

from indy_common.authorize.auth_actions import AuthActionAdd

from plenum.common.exceptions import InvalidClientRequest, OperationError
from plenum.common.request import Request
from plenum.common.txn_util import get_seq_no, get_payload_data
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.handler_interfaces.write_request_handler import WriteRequestHandler


class MintHandler(WriteRequestHandler):

    # it is not really clear what should be returned here for XFER
    def gen_state_key(self, txn):
        pass

    def __init__(self, database_manager: DatabaseManager, write_req_validator):
        super().__init__(database_manager, TokenTransactions.MINT_PUBLIC.value, TOKEN_LEDGER_ID)
        self._write_req_validator = write_req_validator

    def static_validation(self, request: Request):
        error = txn_mint_public_validate(request)

        if error:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       error)

    def dynamic_validation(self, request: Request):
        return self._write_req_validator.validate(request,
                                                  [AuthActionAdd(txn_type=MINT_PUBLIC,
                                                                 field="*",
                                                                 value="*")])

    def update_state(self, txn, prev_result, is_committed=False):
        try:
            payload = get_payload_data(txn)
            seq_no = get_seq_no(txn)
            for output in payload[OUTPUTS]:
                add_new_output(self.state,
                               self.database_manager.get_store("utxo_cache"),
                               Output(output["address"], seq_no, output["amount"]),
                               is_committed=is_committed)
        except UTXOError as ex:
            error = 'Exception {} while updating state'.format(ex)
            raise OperationError(error)
