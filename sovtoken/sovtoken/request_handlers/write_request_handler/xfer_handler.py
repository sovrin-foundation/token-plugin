from typing import Optional

from sovtoken import TokenTransactions
from sovtoken.exceptions import UTXOError

from indy_common.authorize.auth_actions import AuthActionAdd
from sovtoken.constants import INPUTS, OUTPUTS, XFER_PUBLIC, TOKEN_LEDGER_ID, UTXO_CACHE_LABEL, SIGS
from sovtoken.messages.txn_validator import txn_xfer_public_validate
from sovtoken.request_handlers.token_utils import TokenStaticHelper
from sovtoken.types import Output

from plenum.common.constants import ED25519
from plenum.common.exceptions import InvalidClientMessageException, InvalidClientRequest, OperationError
from plenum.common.request import Request
from plenum.common.txn_util import get_payload_data, get_seq_no, add_sigs_to_txn
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

    def dynamic_validation(self, request: Request, req_pp_time: Optional[int]):
        self._do_validate_inputs_ouputs(request)
        return self._write_req_validator.validate(request, [AuthActionAdd(txn_type=XFER_PUBLIC,
                                                                          field="*",
                                                                          value="*")])

    def additional_dynamic_validation(self, request, req_pp_time: Optional[int]):
        pass

    @property
    def utxo_cache(self):
        return self.database_manager.get_store(UTXO_CACHE_LABEL)

    def update_state(self, txn, prev_result, request, is_committed=False):
        try:
            payload = get_payload_data(txn)
            for inp in payload[INPUTS]:
                TokenStaticHelper.spend_input(
                            self.state,
                            self.utxo_cache,
                            inp["address"],
                            inp["seqNo"],
                            is_committed=is_committed)
            for output in payload[OUTPUTS]:
                seq_no = get_seq_no(txn)
                TokenStaticHelper.add_new_output(
                               self.state,
                               self.utxo_cache,
                               Output(output["address"],
                                      seq_no,
                                      output["amount"]),
                               is_committed=is_committed)
        except UTXOError as ex:
            error = 'Exception {} while updating state'.format(ex)
            raise OperationError(error)

    def _req_to_txn(self, req: Request):
        sigs = req.operation.pop(SIGS)
        txn = super()._req_to_txn(req)
        req.operation[SIGS] = sigs
        sigs = [(i["address"], s) for i, s in zip(req.operation[INPUTS], sigs)]
        add_sigs_to_txn(txn, sigs, sig_type=ED25519)
        return txn

    def _do_validate_inputs_ouputs(self, request):
        try:
            sum_in = TokenStaticHelper.sum_inputs(
                                self.utxo_cache,
                                request,
                                is_committed=False)

            sum_out = TokenStaticHelper.sum_outputs(request)
        except Exception as ex:
            if isinstance(ex, InvalidClientMessageException):
                raise ex
            error = 'Exception {} while processing inputs/outputs'.format(ex)
            raise InvalidClientMessageException(request.identifier,
                                                getattr(request, 'reqId', None),
                                                error)
        else:
            return TokenStaticHelper.validate_given_inputs_outputs(sum_in, sum_out, sum_out, request)
