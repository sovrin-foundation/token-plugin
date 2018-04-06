from common.serializers.json_serializer import JsonSerializer
from common.serializers.serialization import serialize_msg_for_signing
from ledger.util import F
from plenum.common.constants import TXN_TYPE, TRUSTEE
from plenum.common.exceptions import UnauthorizedClientRequest, \
    InvalidClientRequest, InsufficientCorrectSignatures
from plenum.common.request import Request
from plenum.common.txn_util import reqToTxn
from plenum.common.types import f
from plenum.persistence.util import txnsWithSeqNo
from plenum.server.domain_req_handler import DomainRequestHandler
from plenum.server.plugin.fees.src.constants import FEE, GET_FEES, FEES, REF
from plenum.server.plugin.fees.src.fee_req_handler import FeeReqHandler
from plenum.server.plugin.fees.src.messages.fields import FeesStructureField
from plenum.server.plugin.token.src.client_authnr import AddressSigVerifier
from plenum.server.plugin.token.src.constants import INPUTS, OUTPUTS, \
    XFER_PUBLIC
from plenum.server.plugin.token.src.token_req_handler import TokenReqHandler
from plenum.server.plugin.token.src.types import Output


class StaticFeesReqHandler(FeeReqHandler):
    valid_txn_types = {FEE, GET_FEES}
    query_types = {GET_FEES, }
    _fees_validator = FeesStructureField()
    MinSendersForFees = 4
    fees_state_key = b'fees'
    state_serializer = JsonSerializer()

    def __init__(self, ledger, state, token_ledger, token_state, utxo_cache,
                 domain_state):
        super().__init__(ledger, state)
        self.token_ledger = token_ledger
        self.token_state = token_state
        self.utxo_cache = utxo_cache
        self.domain_state = domain_state

        # In-memory map of fees, changes on FEE txns
        self.fees = self._get_fees(is_committed=True)

        self.query_handlers = {
            GET_FEES: self.get_fees,
        }

        # Tracks count of transactions paying fees while a batch is being
        # processed. Reset to zero once a batch is created (not committed)
        self.fee_txns_in_current_batch = 0
        # Tracks amount of deducted fees for a transaction
        self.deducted_fees = {}
        # Since inputs are spent in XFER. FIND A BETTER SOLUTION
        self.deducted_fees_xfer = {}
        # Tracks state root for each batch with at least 1 transaction
        # paying fees
        self.uncommitted_state_roots_for_batches = []

    def get_txn_fees(self, request) -> int:
        return self.fees.get(request.operation[TXN_TYPE], 0)

    @staticmethod
    def has_fees(request) -> bool:
        return hasattr(request, FEES) and isinstance(request.fees, list) \
               and len(request.fees) > 0 and isinstance(request.fees[0], list) \
               and len(request.fees[0]) > 0

    @staticmethod
    def get_change_for_fees(request) -> list:
        return request.fees[1] if len(request.fees) == 2 else []

    @staticmethod
    def get_ref_for_txn_fees(ledger_id, seq_no):
        return '{}:{}'.format(ledger_id, seq_no)

    def can_pay_fees(self, request):
        required_fees = self.get_txn_fees(request)
        if required_fees:
            error = None
            operation = request.operation
            if operation[TXN_TYPE] == XFER_PUBLIC:
                # Fees in XFER_PUBLIC is part of operation[INPUTS]
                try:
                    sum_inputs, sum_outputs = TokenReqHandler.get_sum_inputs_outputs(
                        self.utxo_cache,
                        operation[INPUTS],
                        operation[OUTPUTS],
                        is_committed=False)
                except Exception as ex:
                    error = 'Exception {} while processing inputs/outputs'.format(
                        ex)
                else:
                    required_sum_outputs = sum_outputs + required_fees
                    if sum_inputs < required_sum_outputs:
                        error = 'Insufficient funds, sum of inputs is {} ' \
                                'but required is {} (sum of outputs: {}, ' \
                                'fees: {})'.format(sum_inputs,
                                                   required_sum_outputs,
                                                   sum_outputs, required_fees)
                    else:
                        self.deducted_fees_xfer[request.key] = sum_inputs - sum_outputs
            else:
                if not self.has_fees(request):
                    error = 'fees not present or improperly formed'
                if not error:
                    sum_inputs = TokenReqHandler.sum_inputs(self.utxo_cache,
                                                            request.fees[0],
                                                            is_committed=False)
                    change_amount = sum([a for _, a in
                                         self.get_change_for_fees(request)])
                    # TODO: Reconsider, this forces the sender to pay the exact
                    # amount of fees, not more, not less
                    if sum_inputs != (change_amount + required_fees):
                        error = 'Insufficient fees, sum of inputs is {} and sum ' \
                                'of change and fees is {}'.format(
                                 sum_inputs, change_amount+required_fees)
            if error:
                raise UnauthorizedClientRequest(request.identifier,
                                                request.reqId,
                                                error)

    # TODO: Fix this to match signature of `FeeReqHandler` and extract
    # the params from `kwargs`
    def deduct_fees(self, request, cons_time, ledger_id, seq_no, txn):
        operation = request.operation
        if operation[TXN_TYPE] == XFER_PUBLIC:
            if request.key in self.deducted_fees_xfer:
                self.deducted_fees[seq_no] = self.deducted_fees_xfer.pop(request.key)
        else:
            if self.has_fees(request):
                inputs, outputs = getattr(request, f.FEES.nm)
                # This is correct since FEES is changed from config ledger whose
                # transactions have no fees
                fees = self.get_txn_fees(request)
                txn = {
                    INPUTS: inputs,
                    OUTPUTS: outputs,
                    REF: self.get_ref_for_txn_fees(ledger_id, seq_no),
                    FEES: fees
                }
                (start, end), _ = self.token_ledger.appendTxns([
                    TokenReqHandler.transform_txn_for_ledger(txn)])
                self.updateState(txnsWithSeqNo(start, end, [txn]))
                self.fee_txns_in_current_batch += 1

                self.deducted_fees[seq_no] = fees
                return txn

    def doStaticValidation(self, request: Request):
        operation = request.operation
        if operation[TXN_TYPE] in (FEE, GET_FEES):
            error = ''
            if operation[TXN_TYPE] == FEE:
                error = self._fees_validator.validate(operation.get(FEES))
            if error:
                raise InvalidClientRequest(request.identifier, request.reqId,
                                           error)
        else:
            super().doStaticValidation(request)

    def validate(self, req: Request):
        operation = req.operation
        if operation[TXN_TYPE] == FEE:
            error = ''
            senders = req.all_identifiers
            if not all(DomainRequestHandler.get_role(
                    self.domain_state, idr, TRUSTEE) for idr in senders):
                error = 'only Trustees can send this transaction'
            if error:
                raise UnauthorizedClientRequest(req.identifier, req.reqId,
                                                error)
        else:
            super().validate(req)

    def apply(self, req: Request, cons_time: int):
        operation = req.operation
        if operation[TXN_TYPE] == FEE:
            txn = reqToTxn(req, cons_time)
            (start, end), _ = self.ledger.appendTxns(
                [self.transform_txn_for_ledger(txn)])
            self.updateState(txnsWithSeqNo(start, end, [txn]))
            return start, txn
        else:
            return super().apply(req, cons_time)

    def get_query_response(self, request: Request):
        return self.query_handlers[request.operation[TXN_TYPE]](request)

    def updateState(self, txns, isCommitted=False):
        for txn in txns:
            self._update_state_with_single_txn(txn, is_committed=isCommitted)

    def _update_state_with_single_txn(self, txn, is_committed=False):
        if txn.get(TXN_TYPE) == FEE:
            existing_fees = self._get_fees(is_committed=is_committed)
            existing_fees.update(txn[FEES])
            val = self.state_serializer.serialize(existing_fees)
            self.state.set(self.fees_state_key, val)
            self.fees = existing_fees
        else:
            for addr, seq_no, _ in txn[INPUTS]:
                TokenReqHandler.spend_input(state=self.token_state,
                                            utxo_cache=self.utxo_cache,
                                            address=addr, seq_no=seq_no,
                                            is_committed=is_committed)
            for addr, amount in txn[OUTPUTS]:
                TokenReqHandler.add_new_output(state=self.token_state,
                                               utxo_cache=self.utxo_cache,
                                               output=Output(
                                                   addr,
                                                   txn[F.seqNo.name],
                                                   amount),
                                               is_committed=is_committed)

    def get_fees(self, request: Request):
        fees = self._get_fees(is_committed=True)
        result = {f.IDENTIFIER.nm: request.identifier,
                  f.REQ_ID.nm: request.reqId, FEES: fees}
        result.update(request.operation)
        return result

    def _get_fees(self, is_committed=False):
        fees = {}
        try:
            serz = self.state.get(self.fees_state_key,
                                  isCommitted=is_committed)
            if serz:
                fees = self.state_serializer.deserialize(serz)
        except KeyError:
            pass
        return fees

    def post_batch_created(self, ledger_id, state_root):
        if self.fee_txns_in_current_batch > 0:
            state_root = self.token_state.headHash
            self.uncommitted_state_roots_for_batches.append(state_root)
            TokenReqHandler.on_batch_created(self.utxo_cache, state_root)
            self.fee_txns_in_current_batch = 0

    def post_batch_rejected(self, ledger_id):
        if self.fee_txns_in_current_batch > 0:
            TokenReqHandler.on_batch_rejected(self.utxo_cache)
            self.fee_txns_in_current_batch = 0

    def post_batch_committed(self, ledger_id, pp_time, committed_txns,
                             state_root, txn_root):
        committed_seq_nos_with_fees = [t[F.seqNo.name] for t in committed_txns
                                       if t[F.seqNo.name] in self.deducted_fees
                                       and t[TXN_TYPE] != XFER_PUBLIC]
        if len(committed_seq_nos_with_fees) > 0:
            state_root = self.uncommitted_state_roots_for_batches.pop(0)
            # Ignoring txn_root check
            TokenReqHandler.__commit__(self.utxo_cache, self.token_ledger,
                                       self.token_state,
                                       len(committed_seq_nos_with_fees),
                                       state_root, None, pp_time,
                                       ignore_txn_root_check=True)
