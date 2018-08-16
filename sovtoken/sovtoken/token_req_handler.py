from typing import List

import base58
from common.serializers.serialization import proof_nodes_serializer, \
    state_roots_serializer
from plenum.common.txn_util import get_type, get_payload_data, get_seq_no, reqToTxn
from sovtoken.messages.validation import static_req_validation


from plenum.server.ledger_req_handler import LedgerRequestHandler

from plenum.common.constants import TXN_TYPE, TRUSTEE, STATE_PROOF, ROOT_HASH, \
    PROOF_NODES, MULTI_SIGNATURE, ROLE, ED25519, TXN_PAYLOAD_METADATA_REQ_ID
from plenum.common.exceptions import UnauthorizedClientRequest, InvalidClientMessageException, OperationError

from plenum.common.request import Request
from plenum.common.types import f
from plenum.server.domain_req_handler import DomainRequestHandler
from sovtoken.constants import XFER_PUBLIC, MINT_PUBLIC, \
    OUTPUTS, INPUTS, GET_UTXO, ADDRESS, SIGS
from sovtoken.txn_util import add_sigs_to_txn
from sovtoken.types import Output
from sovtoken.util import SortedItems
from sovtoken.utxo_cache import UTXOCache
from sovtoken.exceptions import InsufficientFundsError, ExtraFundsError, InvalidFundsError, UTXOError

from state.trie.pruning_trie import rlp_decode

ALL_IDENTIFIERS = "all_identifiers"

class TokenReqHandler(LedgerRequestHandler):
    write_types = {MINT_PUBLIC, XFER_PUBLIC}
    query_types = {GET_UTXO, }

    MinSendersForPublicMint = 4

    # When set to True, sum of inputs can be greater than outputs but not vice versa.
    # Defaults to False requiring sum of inputs to exactly match outputs, else the txn will be rejected.
    ALLOW_INPUTS_TO_EXCEED_OUTPUTS = False

    def __init__(self, ledger, state, utxo_cache: UTXOCache, domain_state, bls_store):
        super().__init__(ledger, state)
        self.utxo_cache = utxo_cache
        self.domain_state = domain_state
        self.bls_store = bls_store

        self.query_handlers = {
            GET_UTXO: self.get_all_utxo,
        }


    # noinspection PyUnreachableCode
    @staticmethod
    def _validate_mint_public_txn(
        request: Request,
        senders: list,
        required_senders: int
    ):
        # =============
        # Declaration of helper functions.
        # =============

        all_identifiers = getattr(request, ALL_IDENTIFIERS, None)
        req_id = getattr(request, TXN_PAYLOAD_METADATA_REQ_ID, None)

        def _client_exception(error):
            return InvalidClientMessageException(all_identifiers, req_id, error)

        def _unauthorized_exception(error):
            return UnauthorizedClientRequest(all_identifiers, req_id, error)

        def _contains_method(instance, method):
            return callable(getattr(instance, method, None))

        def _is_trustee(sender):
            return _contains_method(sender, "get") and sender.get(ROLE) == TRUSTEE

        # =============
        # Actual validation.
        # =============

        if not isinstance(senders, list):
            raise _client_exception('Senders was not computed to list')

        if len(senders) < required_senders:
            error = 'Request needs at least {} signers but only {} found'. \
                format(required_senders, len(senders))
            raise _unauthorized_exception(error)

        if not all(map(_is_trustee, senders)):
            error = 'only Trustees can send this transaction'
            raise _unauthorized_exception(error)

    @staticmethod
    def _validate_xfer_public_txn(request: Request, sum_inputs: int, sum_outputs: int, allow_inputs_exceed_outputs: bool):
        if not isinstance(sum_inputs, int) or not isinstance(sum_outputs, int):
            raise InvalidClientMessageException(getattr(request, 'identifier', None),
                                                getattr(request, 'reqId', None),
                                                'Summation of input or outputs where not an integer, sum of inputs'
                                                ' is {} and sum of outputs is {}'.format(sum_inputs, sum_outputs))

        if sum_inputs == sum_outputs:
            return  # Equal is valid
        elif sum_inputs > sum_outputs:
            if allow_inputs_exceed_outputs:
                return   # Greater inputs is only valid when allowed
            else:
                error = 'Extra funds, sum of inputs is {} and sum' \
                        ' of outputs is {}'.format(sum_inputs, sum_outputs)
                raise ExtraFundsError(getattr(request, 'identifier', None),
                                      getattr(request, 'reqId', None),
                                      error)

        elif sum_inputs < sum_outputs:
            error = 'Insufficient funds, sum of inputs is {} and sum' \
                    ' of outputs is {}'.format(sum_inputs, sum_outputs)
            raise InsufficientFundsError(getattr(request, 'identifier', None),
                                         getattr(request, 'reqId', None),
                                         error)

        raise InvalidClientMessageException(getattr(request, 'all_identifiers', None),
                                            getattr(request, 'reqId', None),
                                            'Request to not meet minimum requirements')

    def doStaticValidation(self, request: Request):
        static_req_validation(request)

    def validate(self, request: Request):
        req_type = request.operation[TXN_TYPE]
        if req_type == MINT_PUBLIC:
            senders = [DomainRequestHandler.getNymDetails(self.domain_state, idr) for idr in request.all_identifiers]
            return TokenReqHandler._validate_mint_public_txn(request, senders, self.MinSendersForPublicMint)

        elif req_type == XFER_PUBLIC:
            try:
                sum_inputs = TokenReqHandler.sum_inputs(self.utxo_cache,
                                                        request,
                                                        is_committed=False)

                sum_outputs = TokenReqHandler.sum_outputs(request)
            except Exception as ex:
                if isinstance(ex, InvalidClientMessageException):
                    raise ex
                error = 'TException {} while processing inputs/outputs'.format(ex)
                raise InvalidClientMessageException(request.identifier,
                                                    getattr(request, 'reqId', None),
                                                    error)
            else:
                return TokenReqHandler._validate_xfer_public_txn(request,
                                                                 sum_inputs,
                                                                 sum_outputs,
                                                                 self.ALLOW_INPUTS_TO_EXCEED_OUTPUTS)

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
            sigs = [(i[0], s) for i, s in zip(req.operation[INPUTS], sigs)]
            add_sigs_to_txn(txn, sigs, sig_type=ED25519)
        return txn

    def _update_state_mint_public_txn(self, txn, is_committed=False):
        payload = get_payload_data(txn)
        seq_no = get_seq_no(txn)
        for addr, amount in payload[OUTPUTS]:
            self._add_new_output(Output(addr, seq_no, amount),
                                 is_committed=is_committed)

    def _update_state_xfer_public(self, txn, is_committed=False):
        payload = get_payload_data(txn)
        for addr, seq_no in payload[INPUTS]:
            self._spend_input(addr, seq_no, is_committed=is_committed)
        for addr, amount in payload[OUTPUTS]:
            seq_no = get_seq_no(txn)
            self._add_new_output(Output(addr, seq_no, amount),
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
        self.on_batch_created(self.utxo_cache, state_root)

    def onBatchRejected(self):
        self.on_batch_rejected(self.utxo_cache)

    def commit(self, txnCount, stateRoot, txnRoot, pptime) -> List:
        return self.__commit__(self.utxo_cache, self.ledger, self.state,
                               txnCount, stateRoot, txnRoot, pptime, self.ts_store)

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
        return sum(o[1] for o in request.operation[OUTPUTS])

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
    def __commit__(utxo_cache, ledger, state, txnCount, stateRoot, txnRoot,
                   ppTime, ts_store=None):
        r = LedgerRequestHandler._commit(ledger, state, txnCount, stateRoot,
                                         txnRoot, ppTime, ts_store=ts_store)
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
