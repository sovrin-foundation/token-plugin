from sovtoken import TokenTransactions
from sovtoken.exceptions import UTXOError

from indy_common.authorize.auth_actions import AuthActionAdd
from sovtoken.constants import INPUTS, OUTPUTS, XFER_PUBLIC, TOKEN_LEDGER_ID, UTXO_CACHE_LABEL
from sovtoken.messages.txn_validator import txn_xfer_public_validate
from sovtoken.request_handlers.token_utils import spend_input, add_new_output, sum_inputs, sum_outputs, \
    validate_given_inputs_outputs
from sovtoken.types import Output

from plenum.common.exceptions import InvalidClientMessageException, InvalidClientRequest, OperationError
from plenum.common.request import Request
from plenum.common.txn_util import get_payload_data, get_seq_no
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.handler_interfaces.write_request_handler import WriteRequestHandler


class XferHandler(WriteRequestHandler):

    # it is not really clear what should be returned here for MINT
    def gen_state_key(self, txn):
        pass

    def __init__(self, database_manager: DatabaseManager, write_req_validator):
        super().__init__(database_manager, TokenTransactions.XFER_PUBLIC.value, TOKEN_LEDGER_ID)
        self._write_req_validator = write_req_validator

    def static_validation(self, request: Request):
        error = txn_xfer_public_validate(request)
        if error:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       error)

    def dynamic_validation(self, request: Request):
        self._do_validate_inputs_ouputs(request)
        return self._write_req_validator.validate(request, [AuthActionAdd(txn_type=XFER_PUBLIC,
                                                                          field="*",
                                                                          value="*")])

    @property
    def utxo_cache(self):
        return self.database_manager.get_store(UTXO_CACHE_LABEL)

    def update_state(self, txn, prev_result, request, is_committed=False):
        try:
            payload = get_payload_data(txn)
            for inp in payload[INPUTS]:
                spend_input(self.state,
                            self.utxo_cache,
                            inp["address"],
                            inp["seqNo"],
                            is_committed=is_committed)
            for output in payload[OUTPUTS]:
                seq_no = get_seq_no(txn)
                add_new_output(self.state,
                               self.utxo_cache,
                               Output(output["address"],
                                      seq_no,
                                      output["amount"]),
                               is_committed=is_committed)
        except UTXOError as ex:
            error = 'Exception {} while updating state'.format(ex)
            raise OperationError(error)

    def _do_validate_inputs_ouputs(self, request):
        try:
            sum_in = sum_inputs(self.utxo_cache,
                                request,
                                is_committed=False)

            sum_out = sum_outputs(request)
        except Exception as ex:
            if isinstance(ex, InvalidClientMessageException):
                raise ex
            error = 'Exception {} while processing inputs/outputs'.format(ex)
            raise InvalidClientMessageException(request.identifier,
                                                getattr(request, 'reqId', None),
                                                error)
        else:
            return validate_given_inputs_outputs(sum_in, sum_out, sum_out, request)
