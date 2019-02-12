from typing import List, Optional

import base58
from common.serializers.serialization import proof_nodes_serializer, \
    state_roots_serializer
from plenum.common.txn_util import get_type, get_payload_data, get_seq_no, reqToTxn
from sovtoken.messages.validation import static_req_validation

from plenum.server.ledger_req_handler import LedgerRequestHandler

from plenum.common.constants import TXN_TYPE, TRUSTEE, STATE_PROOF, ROOT_HASH, \
    PROOF_NODES, MULTI_SIGNATURE, ED25519
from plenum.common.exceptions import InvalidClientMessageException, OperationError

from plenum.common.request import Request
from plenum.common.types import f
from sovtoken.constants import XFER_PUBLIC, MINT_PUBLIC, \
    OUTPUTS, INPUTS, GET_UTXO, ADDRESS, SIGS
from sovtoken.txn_util import add_sigs_to_txn
from sovtoken.types import Output
from sovtoken.util import SortedItems, validate_multi_sig_txn
from sovtoken.utxo_cache import UTXOCache
from sovtoken.exceptions import InsufficientFundsError, ExtraFundsError, InvalidFundsError, UTXOError, TokenValueError
from plenum.common.ledger_uncommitted_tracker import LedgerUncommittedTracker
from state.trie.pruning_trie import rlp_decode

from state.pruning_state import PruningState

from plenum.common.ledger import Ledger


class TokenReqHandler(LedgerRequestHandler):
    write_types = {MINT_PUBLIC, XFER_PUBLIC}
    query_types = {GET_UTXO, }

    MinSendersForPublicMint = 3

    def __init__(self, ledger, state: PruningState, utxo_cache: UTXOCache, domain_state, bls_store):
        super().__init__(ledger, state)
        self.utxo_cache = utxo_cache
        self.domain_state = domain_state
        self.bls_store = bls_store
        self.tracker = LedgerUncommittedTracker(state.committedHeadHash, ledger.size)
        self.query_handlers = {
            GET_UTXO: self.get_all_utxo,
        }

    def handle_xfer_public_txn(self, request):
        # Currently only sum of inputs is matched with sum of outputs. If anything more is
            # needed then a new function should be created.
        try:
            sum_inputs = TokenReqHandler.sum_inputs(self.utxo_cache,
                                                    request,
                                                    is_committed=False)

            sum_outputs = TokenReqHandler.sum_outputs(request)
        except Exception as ex:
            if isinstance(ex, InvalidClientMessageException):
                raise ex
            error = 'Exception {} while processing inputs/outputs'.format(ex)
            raise InvalidClientMessageException(request.identifier,
                                                getattr(request, 'reqId', None),
                                                error)
        else:
            return TokenReqHandler._validate_xfer_public_txn(request,
                                                             sum_inputs,
                                                             sum_outputs)

    @staticmethod
    def _validate_xfer_public_txn(request: Request, sum_inputs: int, sum_outputs: int):
        TokenReqHandler.validate_given_inputs_outputs(sum_inputs, sum_outputs, sum_outputs, request)

    @staticmethod
    def validate_given_inputs_outputs(inputs_sum, outputs_sum, required_amount, request,
                                      error_msg_suffix: Optional[str]=None):
        """
        Checks three sum values against simple set of rules. inputs_sum must be equal to required_amount. Exceptions
        are raise if it is not equal. The outputs_sum is pass not for checks but to be included in error messages.
        This is confusing but is required in cases where the required amount is different then the sum of outputs (
        in the case of fees).

        :param inputs_sum: the sum of inputs
        :param outputs_sum: the sum of outputs
        :param required_amount: the required amount to validate (could be equal to output_sum, but may be different)
        :param request: the request that is being validated
        :param error_msg_suffix: added message to the error message
        :return: returns if valid or will raise an exception
        """

        if inputs_sum == required_amount:
            return  # Equal is valid
        elif inputs_sum > required_amount:
            error = 'Extra funds, sum of inputs is {} ' \
                    'but required amount: {} -- sum of outputs: {}'.format(inputs_sum, required_amount, outputs_sum)
            if error_msg_suffix and isinstance(error_msg_suffix, str):
                error += ' ' + error_msg_suffix
            raise ExtraFundsError(getattr(request, f.IDENTIFIER.nm, None),
                                  getattr(request, f.REQ_ID.nm, None),
                                  error)

        elif inputs_sum < required_amount:
            error = 'Insufficient funds, sum of inputs is {}' \
                    'but required amount is {}. sum of outputs: {}'.format(inputs_sum, required_amount, outputs_sum)
            if error_msg_suffix and isinstance(error_msg_suffix, str):
                error += ' ' + error_msg_suffix
            raise InsufficientFundsError(getattr(request, f.IDENTIFIER.nm, None),
                                         getattr(request, f.REQ_ID.nm, None),
                                         error)

        raise InvalidClientMessageException(getattr(request, f.IDENTIFIER.nm, None),
                                            getattr(request, f.REQ_ID.nm, None),
                                            'Request to not meet minimum requirements')

    def doStaticValidation(self, request: Request):
        static_req_validation(request)

    def validate(self, request: Request):
        req_type = request.operation[TXN_TYPE]
        if req_type == MINT_PUBLIC:
            return validate_multi_sig_txn(request, TRUSTEE, self.domain_state, self.MinSendersForPublicMint)

        elif req_type == XFER_PUBLIC:
            return self.handle_xfer_public_txn(request)

        raise InvalidClientMessageException(request.identifier,
                                            getattr(request, 'reqId', None),
                                            'Unsupported request type - {}'.format(req_type))

    @staticmethod
    def transform_txn_for_ledger(txn):
        """
        Token TXNs does not need to be transformed
        """
        return txn

    def _reqToTxn(self, req: Request):
        """
        Converts the request to a transaction. This is called by LedgerRequestHandler. Not a
        public method. TODO we should consider a more standard approach to inheritance.

        :param req:
        :return: the converted transaction from the Request
        """
        if req.operation[TXN_TYPE] == XFER_PUBLIC:
            sigs = req.operation.pop(SIGS)
        txn = reqToTxn(req)
        if req.operation[TXN_TYPE] == XFER_PUBLIC:
            req.operation[SIGS] = sigs
            sigs = [(i["address"], s) for i, s in zip(req.operation[INPUTS], sigs)]
            add_sigs_to_txn(txn, sigs, sig_type=ED25519)
        return txn

    def _update_state_mint_public_txn(self, txn, is_committed=False):
        payload = get_payload_data(txn)
        seq_no = get_seq_no(txn)
        for output in payload[OUTPUTS]:
            self._add_new_output(Output(output["address"], seq_no, output["amount"]),
                                 is_committed=is_committed)

    def _update_state_xfer_public(self, txn, is_committed=False):
        payload = get_payload_data(txn)
        for inp in payload[INPUTS]:
            self._spend_input(inp["address"], inp["seqNo"], is_committed=is_committed)
        for output in payload[OUTPUTS]:
            seq_no = get_seq_no(txn)
            self._add_new_output(Output(output["address"], seq_no, output["amount"]),
                                 is_committed=is_committed)

    def updateState(self, txns, isCommitted=False):
        try:
            for txn in txns:
                typ = get_type(txn)
                if typ == MINT_PUBLIC:
                    self._update_state_mint_public_txn(txn, is_committed=isCommitted)

                if typ == XFER_PUBLIC:
                    self._update_state_xfer_public(txn, is_committed=isCommitted)
        except UTXOError as ex:
            error = 'Exception {} while updating state'.format(ex)
            raise OperationError(error)

    def _spend_input(self, address, seq_no, is_committed=False):
        self.spend_input(self.state, self.utxo_cache, address, seq_no,
                         is_committed=is_committed)

    def _add_new_output(self, output: Output, is_committed=False):
        self.add_new_output(self.state, self.utxo_cache, output,
                            is_committed=is_committed)

    def onBatchCreated(self, state_root):
        self.on_batch_created(self.utxo_cache, self.tracker, self.ledger, state_root)

    def onBatchRejected(self, ledger_id):
        self.on_batch_rejected(self.utxo_cache, self.tracker, self.state, self.ledger)

    def commit(self, txnCount, stateRoot, txnRoot, pptime) -> List:
        return self.__commit__(self.utxo_cache, self.ledger, self.state,
                               txnCount, stateRoot, txnRoot, pptime, self.tracker,
                               self.ts_store)

    def get_query_response(self, request: Request):
        return self.query_handlers[request.operation[TXN_TYPE]](request)

    def get_all_utxo(self, request: Request):
        address = request.operation[ADDRESS]
        encoded_root_hash = state_roots_serializer.serialize(
            bytes(self.state.committedHeadHash))
        proof, rv = self.state.generate_state_proof_for_keys_with_prefix(address,
                                                                         serialize=True,
                                                                         get_value=True)
        multi_sig = self.bls_store.get(encoded_root_hash)
        if multi_sig:
            encoded_proof = proof_nodes_serializer.serialize(proof)
            proof = {
                MULTI_SIGNATURE: multi_sig.as_dict(),
                ROOT_HASH: encoded_root_hash,
                PROOF_NODES: encoded_proof
            }
        else:
            proof = {}

        # The outputs need to be returned in sorted order since each node's reply should be same.
        # Since no of outputs can be large, a concious choice to not use `operator.attrgetter` on an
        # already constructed list was made
        outputs = SortedItems()
        for k, v in rv.items():
            addr, seq_no = self.parse_state_key(k.decode())
            amount = rlp_decode(v)[0]
            if not amount:
                continue
            outputs.add(Output(addr, int(seq_no), int(amount)))

        result = {f.IDENTIFIER.nm: request.identifier,
                  f.REQ_ID.nm: request.reqId, OUTPUTS: outputs.sorted_list}
        if proof:
            result[STATE_PROOF] = proof

        result.update(request.operation)
        return result

    def _sum_inputs(self, req: Request, is_committed=False) -> int:
        return self.sum_inputs(self.utxo_cache, req,
                               is_committed=is_committed)

    @staticmethod
    def create_state_key(address: str, seq_no: int) -> bytes:
        return ':'.join([address, str(seq_no)]).encode()

    @staticmethod
    def parse_state_key(key: str) -> List[str]:
        return key.split(':')

    @staticmethod
    def sum_inputs(utxo_cache: UTXOCache, request: Request,
                   is_committed=False) -> int:
        try:
            inputs = request.operation[INPUTS]
            return utxo_cache.sum_inputs(inputs, is_committed=is_committed)
        except UTXOError as ex:
            raise InvalidFundsError(request.identifier, request.reqId, '{}'.format(ex))

    @staticmethod
    def sum_outputs(request: Request) -> int:
        return sum(o["amount"] for o in request.operation[OUTPUTS])

    @staticmethod
    def spend_input(state, utxo_cache, address, seq_no, is_committed=False):
        state_key = TokenReqHandler.create_state_key(address, seq_no)
        state.set(state_key, b'')
        utxo_cache.spend_output(Output(address, seq_no, None),
                                is_committed=is_committed)

    @staticmethod
    def add_new_output(state, utxo_cache, output: Output, is_committed=False):
        address = output.address
        seq_no = output.seqNo
        amount = output.amount
        state_key = TokenReqHandler.create_state_key(address, seq_no)
        state.set(state_key, str(amount).encode())
        utxo_cache.add_output(output, is_committed=is_committed)

    @staticmethod
    def __commit__(utxo_cache, ledger, state, txnCount, stateRoot, txnRoot,
                   ppTime, tracker, ts_store=None):
        r = LedgerRequestHandler._commit(ledger, state, txnCount, stateRoot,
                                         txnRoot, ppTime, ts_store=ts_store)
        TokenReqHandler._commit_to_utxo_cache(utxo_cache, stateRoot)
        tracker.commit_batch()
        return r

    @staticmethod
    def _commit_to_utxo_cache(utxo_cache, state_root):
        state_root = base58.b58decode(state_root.encode()) if isinstance(
            state_root, str) else state_root
        if utxo_cache.first_batch_idr != state_root:
            raise TokenValueError(
                'state_root', state_root,
                ("equal to utxo_cache.first_batch_idr hash {}"
                 .format(utxo_cache.first_batch_idr))
            )
        utxo_cache.commit_batch()

    @staticmethod
    def on_batch_created(utxo_cache, tracker: LedgerUncommittedTracker, ledger: Ledger, state_root):
        tracker.apply_batch(state_root, ledger.uncommitted_size)
        utxo_cache.create_batch_from_current(state_root)

    @staticmethod
    def on_batch_rejected(utxo_cache, tracker: LedgerUncommittedTracker, state: PruningState, ledger: Ledger):
        uncommitted_hash, txn_count = tracker.reject_batch()
        if txn_count == 0:
            return
        state.revertToHead(uncommitted_hash)
        ledger.discardTxns(txn_count)

        utxo_cache.reject_batch()
