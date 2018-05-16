from typing import List, Iterable

import base58

from ledger.util import F
from plenum.common.constants import TXN_TYPE, TRUSTEE
from plenum.common.exceptions import InvalidClientRequest, \
    UnauthorizedClientRequest
from plenum.common.messages.fields import IterableField
from plenum.common.request import Request
from plenum.common.txn_util import reqToTxn
from plenum.common.types import f
from plenum.persistence.util import txnsWithSeqNo
from plenum.server.domain_req_handler import DomainRequestHandler
from plenum.server.plugin.token.src.constants import XFER_PUBLIC, MINT_PUBLIC, \
    OUTPUTS, INPUTS, GET_UTXO, ADDRESSES
from plenum.server.plugin.token.src.messages.fields import PublicOutputField, \
    PublicInputsField, PublicOutputsField, PublicAddressesField
from plenum.server.plugin.token.src.types import Output
from plenum.server.plugin.token.src.utxo_cache import UTXOCache
from plenum.server.req_handler import RequestHandler


# TODO: Rename to `PaymentReqHandler`
class TokenReqHandler(RequestHandler):
    write_types = {MINT_PUBLIC, XFER_PUBLIC}
    query_types = {GET_UTXO, }

    _public_output_validator = IterableField(PublicOutputField())
    _public_outputs_validator = PublicOutputsField()
    _public_inputs_validator = PublicInputsField()
    _public_addresses_validator = PublicAddressesField()
    MinSendersForPublicMint = 4

    def __init__(self, ledger, state, utxo_cache: UTXOCache, domain_state):
        super().__init__(ledger, state)
        self.utxo_cache = utxo_cache
        self.domain_state = domain_state

        self.query_handlers = {
            GET_UTXO: self.get_all_utxo,
        }

    def _MINT_PUBLIC_validate(self, request: Request):
        operation = request.operation
        if operation[TXN_TYPE] == MINT_PUBLIC:
            return self._operation_outputs_validate(request)

    def _XFER_PUBLIC_validate(self, request: Request):
        operation = request.operation
        if operation[TXN_TYPE] == XFER_PUBLIC:
            error = self._operation_outputs_validate(request)
            if error:
                return error
            else:
                error = self._operation_inputs_validate(request)
            return error

    def _GET_UTXO_validate(self, request: Request):
        operation = request.operation
        if operation[TXN_TYPE] == GET_UTXO:
            return self._operation_addresses_validate(request)

    def _operation_outputs_validate(self, request: Request):
        operation = request.operation
        if OUTPUTS not in operation:
            raise InvalidClientRequest(request.identifier, request.reqId,
                                       "{} needs to be present".
                                       format(OUTPUTS))
        return self._public_outputs_validator.validate(operation[OUTPUTS])

    def _operation_inputs_validate(self, request: Request):
        operation = request.operation
        if INPUTS not in operation:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       "{} needs to be present".
                                       format(INPUTS))
        return self._public_inputs_validator.validate(operation[INPUTS])

    def _operation_addresses_validate(self, request: Request):
        operation = request.operation
        if ADDRESSES not in operation:
            error = '{} needs to be provided'.format(ADDRESSES)
        else:
            error = self._public_addresses_validator.validate(operation[ADDRESSES])
        if error:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId, error)

    def doStaticValidation(self, request: Request):
        operation = request.operation
        if operation[TXN_TYPE] in (MINT_PUBLIC, XFER_PUBLIC, GET_UTXO):
            # This is the python way of doing a switch statement.
            # It seems cleaner than a stack of if/elif/else
            txn_type_switch = {
                MINT_PUBLIC: self._MINT_PUBLIC_validate,
                XFER_PUBLIC: self._XFER_PUBLIC_validate,
                GET_UTXO: self._GET_UTXO_validate
            }
            error = txn_type_switch[operation[TXN_TYPE]](request)
            if error:
                raise InvalidClientRequest(request.identifier,
                                           request.reqId,
                                           error)
        else:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       "Invalid type in operation",
                                       operation[TXN_TYPE])

    def validate(self, request: Request):
        operation = request.operation
        error = ''
        if operation[TXN_TYPE] == MINT_PUBLIC:
            senders = request.all_identifiers
            if not all(DomainRequestHandler.get_role(
                    self.domain_state, idr, TRUSTEE) for idr in senders):
                error = 'only Trustees can send this transaction'
            if len(senders) < self.MinSendersForPublicMint:
                error = 'Need at least {} but only {} found'.\
                    format(self.MinSendersForPublicMint, len(senders))

        if operation[TXN_TYPE] == XFER_PUBLIC:
            try:
                sum_inputs, sum_outputs = self.get_sum_inputs_outputs(
                    self.utxo_cache,
                    operation[INPUTS],
                    operation[OUTPUTS],
                    is_committed=False)
            except Exception as ex:
                error = 'Exception {} while processing inputs/outputs'.format(ex)
            else:
                if sum_inputs < sum_outputs:
                    error = 'Insufficient funds, sum of inputs is {} and sum' \
                            ' of outputs is {}'.format(sum_inputs, sum_outputs)

        if error:
            raise UnauthorizedClientRequest(request.identifier,
                                            request.reqId,
                                            error)

    def apply(self, req: Request, cons_time: int):
        txn = reqToTxn(req, cons_time)
        (start, end), _ = self.ledger.appendTxns(
            [self.transform_txn_for_ledger(txn)])
        self.updateState(txnsWithSeqNo(start, end, [txn]))
        return start, txn

    @staticmethod
    def transform_txn_for_ledger(txn):
        """
        Some transactions need to be updated before they can be stored in the
        ledger
        """
        return txn

    def updateState(self, txns, isCommitted=False):
        for txn in txns:
            self._update_state_with_single_txn(txn, is_committed=isCommitted)

    def _update_state_with_single_txn(self, txn, is_committed=False):
        if txn[TXN_TYPE] == MINT_PUBLIC:
            for addr, amount in txn[OUTPUTS]:
                self._add_new_output(Output(addr, txn[F.seqNo.name], amount),
                                     is_committed=is_committed)
        if txn[TXN_TYPE] == XFER_PUBLIC:
            for addr, seq_no, _ in txn[INPUTS]:
                self._spend_input(addr, seq_no, is_committed=is_committed)
            for addr, amount in txn[OUTPUTS]:
                self._add_new_output(Output(addr, txn[F.seqNo.name], amount),
                                     is_committed=is_committed)

    def _spend_input(self, address, seq_no, is_committed=False):
        self.spend_input(self.state, self.utxo_cache, address, seq_no,
                         is_committed=is_committed)

    def _add_new_output(self, output: Output, is_committed=False):
        self.add_new_output(self.state, self.utxo_cache, output,
                            is_committed=is_committed)

    def onBatchCreated(self, state_root):
        self.on_batch_created(self.utxo_cache, state_root)

    def onBatchRejected(self):
        self.on_batch_rejected(self.utxo_cache)

    def commit(self, txnCount, stateRoot, txnRoot, pptime) -> List:
        return self.__commit__(self.utxo_cache, self.ledger, self.state,
                               txnCount, stateRoot, txnRoot, pptime)

    def get_query_response(self, request: Request):
        return self.query_handlers[request.operation[TXN_TYPE]](request)

    def get_all_utxo(self, request: Request):
        addresses = request.operation[ADDRESSES]
        outputs = [
            utxo
            for address in addresses
            for utxo in self.utxo_cache.get_unspent_outputs(address,is_committed=True)
        ]

        result = {f.IDENTIFIER.nm: request.identifier,
                  f.REQ_ID.nm: request.reqId, OUTPUTS: outputs}
        result.update(request.operation)
        return result

    def _sum_inputs(self, inputs: Iterable, is_committed=False) -> int:
        return self.sum_inputs(self.utxo_cache, inputs,
                               is_committed=is_committed)

    @staticmethod
    def create_state_key(address: str, seq_no: int) -> bytes:
        return ':'.join([address, str(seq_no)]).encode()

    @staticmethod
    def sum_inputs(utxo_cache: UTXOCache, inputs: Iterable,
                   is_committed=False) -> int:
        output_val = 0
        for addr, seq_no, _ in inputs:
            try:
                output_val += utxo_cache.get_output(
                    Output(addr, seq_no, None),
                    is_committed=is_committed).value
            except KeyError:
                continue
        return output_val

    @staticmethod
    def spend_input(state, utxo_cache, address, seq_no, is_committed=False):
        state_key = TokenReqHandler.create_state_key(address, seq_no)
        state.set(state_key, b'')
        utxo_cache.spend_output(Output(address, seq_no, None),
                                is_committed=is_committed)

    @staticmethod
    def add_new_output(state, utxo_cache, output: Output, is_committed=False):
        address, seq_no, amount = output
        state_key = TokenReqHandler.create_state_key(address, seq_no)
        state.set(state_key, str(amount).encode())
        utxo_cache.add_output(output, is_committed=is_committed)

    @staticmethod
    def get_sum_inputs_outputs(utxo_cache, inputs, outputs, is_committed=False):
        sum_inputs = TokenReqHandler.sum_inputs(utxo_cache, inputs,
                                                is_committed=is_committed)
        sum_outputs = sum(o[1] for o in outputs)
        return sum_inputs, sum_outputs

    @staticmethod
    def __commit__(utxo_cache, ledger, state, txnCount, stateRoot, txnRoot,
                   ppTime, ignore_txn_root_check=False):
        r = RequestHandler._commit(ledger, state, txnCount, stateRoot, txnRoot,
                                   ppTime,
                                   ignore_txn_root_check=ignore_txn_root_check)
        TokenReqHandler._commit_to_utxo_cache(utxo_cache, stateRoot)
        return r

    @staticmethod
    def _commit_to_utxo_cache(utxo_cache, state_root):
        state_root = base58.b58decode(state_root.encode()) if isinstance(
            state_root, str) else state_root
        assert utxo_cache.first_batch_idr == state_root
        utxo_cache.commit_batch()

    @staticmethod
    def on_batch_created(utxo_cache, state_root):
        utxo_cache.create_batch_from_current(state_root)

    @staticmethod
    def on_batch_rejected(utxo_cache):
        utxo_cache.reject_batch()
