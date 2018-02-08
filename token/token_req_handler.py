from typing import Tuple, List, Iterable

import base58

from ledger.util import F
from plenum.common.constants import TXN_TYPE, TRUSTEE, DATA
from plenum.common.exceptions import InvalidClientRequest, \
    UnauthorizedClientRequest
from plenum.common.messages.fields import IterableField
from plenum.common.request import Request
from plenum.common.txn_util import reqToTxn
from plenum.common.types import f
from plenum.persistence.util import txnsWithSeqNo
from plenum.server.domain_req_handler import DomainRequestHandler
from plenum.server.plugin.token.constants import XFER_PUBLIC, MINT_PUBLIC, \
    OUTPUTS, INPUTS, GET_UTXO, ADDRESS
from plenum.server.plugin.token.messages.fields import PublicOutputField, \
    PublicInputsField, PublicOutputsField
from plenum.server.plugin.token.types import Output
from plenum.server.plugin.token.utxo_cache import UTXOCache
from plenum.server.req_handler import RequestHandler


class TokenReqHandler(RequestHandler):
    valid_txn_types = {MINT_PUBLIC, XFER_PUBLIC, GET_UTXO}
    query_types = {GET_UTXO, }
    _public_output_validator = IterableField(PublicOutputField())
    _public_outputs_validator = PublicOutputsField()
    _public_inputs_validator = PublicInputsField()
    MinSendersForPublicMint = 4

    def __init__(self, ledger, state, utxo_cache: UTXOCache, domain_state):
        super().__init__(ledger, state)
        self.utxo_cache = utxo_cache
        self.domain_state = domain_state

        self.query_handlers = {
            GET_UTXO: self.get_all_utxo,
        }

    def doStaticValidation(self, request: Request):
        operation = request.operation
        error = ''
        if operation[TXN_TYPE] in (MINT_PUBLIC, XFER_PUBLIC):
            if OUTPUTS not in operation:
                raise InvalidClientRequest(request.identifier, request.reqId,
                                           "{} needs to be present".
                                           format(OUTPUTS))
            error = self._public_outputs_validator.validate(operation[OUTPUTS])
            if not error:
                if operation[TXN_TYPE] == XFER_PUBLIC:
                    if INPUTS not in operation:
                        raise InvalidClientRequest(request.identifier,
                                                   request.reqId,
                                                   "{} needs to be present".
                                                   format(INPUTS))
                    error = self._public_inputs_validator.validate(
                        operation[INPUTS])

        if operation[TXN_TYPE] == GET_UTXO:
            if ADDRESS not in operation:
                error = '{} needs to be provided'.format(ADDRESS)
            else:
                error = self._public_output_validator.inner_field_type.\
                    public_address_field.validate(operation[ADDRESS])
        if error:
            raise InvalidClientRequest(request.identifier, request.reqId,
                                       error)

    def validate(self, req: Request):
        operation = req.operation
        error = ''
        if operation[TXN_TYPE] == MINT_PUBLIC:
            senders = req.all_identifiers
            if not all(DomainRequestHandler.get_role(
                    self.domain_state, idr, TRUSTEE) for idr in senders):
                error = 'only Trustees can send this transaction'
            if len(senders) < self.MinSendersForPublicMint:
                error = 'Need at least {} but only {} found'.\
                    format(self.MinSendersForPublicMint, len(senders))

        if operation[TXN_TYPE] == XFER_PUBLIC:
            try:
                sum_inputs = self._sum_inputs(operation[INPUTS],
                                              is_committed=False)
            except Exception as ex:
                error = 'Exception {} while processing inputs'.format(ex)
            else:
                sum_outputs = sum(o[1] for o in operation[OUTPUTS])
                if sum_inputs < sum_outputs:
                    error = 'Insufficient funds, sum of inputs is {} and sum' \
                            ' of outputs is {}'.format(sum_inputs, sum_outputs)

        if error:
            raise UnauthorizedClientRequest(req.identifier, req.reqId,
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
            for addr, seq_no in txn[INPUTS]:
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
        self.utxo_cache.create_batch_from_current(state_root)

    def onBatchRejected(self):
        self.utxo_cache.reject_batch()

    def commit(self, txnCount, stateRoot, txnRoot) -> List:
        r = super().commit(txnCount, stateRoot, txnRoot)
        stateRoot = base58.b58decode(stateRoot.encode())
        assert self.utxo_cache.first_batch_idr == stateRoot
        self.utxo_cache.commit_batch()
        return r

    def get_query_response(self, request: Request):
        return self.query_handlers[request.operation[TXN_TYPE]](request)

    def get_all_utxo(self, request: Request):
        address = request.operation[ADDRESS]
        outputs = self.utxo_cache.get_unspent_outputs(address,
                                                      is_committed=True)
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
        return sum([utxo_cache.get_output(
            Output(addr, seq_no, None), is_committed=is_committed).value
                    for addr, seq_no in inputs])

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
