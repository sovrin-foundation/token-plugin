from typing import List, Iterable

import base58
from common.serializers.serialization import proof_nodes_serializer, \
    state_roots_serializer
from plenum.common.txn_util import reqToTxn, get_type, get_payload_data, get_seq_no
#, add_sigs_to_txn
# TODO remove that onece https://github.com/hyperledger/indy-plenum/pull/767 is merged
# (should be imported from plenum.common.txn_util)
from sovtoken.txn_util import add_sigs_to_txn

from plenum.server.ledger_req_handler import LedgerRequestHandler

from plenum.common.constants import TXN_TYPE, TRUSTEE, STATE_PROOF, ROOT_HASH, \
    PROOF_NODES, ED25519, MULTI_SIGNATURE
from plenum.common.exceptions import InvalidClientRequest, \
    UnauthorizedClientRequest
from plenum.common.messages.fields import IterableField
from plenum.common.request import Request
from plenum.common.types import f
from plenum.server.domain_req_handler import DomainRequestHandler
from sovtoken.constants import XFER_PUBLIC, MINT_PUBLIC, \
    OUTPUTS, INPUTS, GET_UTXO, ADDRESS, SIGS
from sovtoken.messages.fields import PublicOutputField, \
    PublicInputsField, PublicOutputsField
from sovtoken.types import Output
from sovtoken.utxo_cache import UTXOCache


# TODO: Rename to `PaymentReqHandler`
from state.trie.pruning_trie import rlp_decode


class TokenReqHandler(LedgerRequestHandler):
    write_types = {MINT_PUBLIC, XFER_PUBLIC}
    query_types = {GET_UTXO, }

    _public_output_validator = IterableField(PublicOutputField())
    _public_outputs_validator = PublicOutputsField()
    _public_inputs_validator = PublicInputsField()
    MinSendersForPublicMint = 4

    def __init__(self, ledger, state, utxo_cache: UTXOCache, domain_state, bls_store):
        super().__init__(ledger, state)
        self.utxo_cache = utxo_cache
        self.domain_state = domain_state
        self.bls_store = bls_store

        self.query_handlers = {
            GET_UTXO: self.get_all_utxo,
        }

    @staticmethod
    def _MINT_PUBLIC_validate(request: Request):
        operation = request.operation
        if operation[TXN_TYPE] == MINT_PUBLIC:
            return TokenReqHandler._operation_outputs_validate(request)

    @staticmethod
    def _XFER_PUBLIC_validate(request: Request):
        operation = request.operation
        if operation[TXN_TYPE] == XFER_PUBLIC:
            error = TokenReqHandler._operation_outputs_validate(request)
            if error:
                return error
            else:
                error = TokenReqHandler._operation_inputs_validate(request)
            return error

    @staticmethod
    def _GET_UTXO_validate(request: Request):
        operation = request.operation
        if operation[TXN_TYPE] == GET_UTXO:
            return TokenReqHandler._operation_address_validate(request)

    @staticmethod
    def _operation_outputs_validate(request: Request):
        operation = request.operation
        if OUTPUTS not in operation:
            raise InvalidClientRequest(request.identifier, request.reqId,
                                       "{} needs to be present".
                                       format(OUTPUTS))
        return TokenReqHandler._public_outputs_validator.validate(operation[OUTPUTS])

    @staticmethod
    def _operation_inputs_validate(request: Request):
        operation = request.operation
        if INPUTS not in operation:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       "{} needs to be present".
                                       format(INPUTS))
        if SIGS not in operation:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       "{} needs to be present".
                                       format(SIGS))
        # THIS IS TEMPORARY. The new format of requests will take an array of signatures
        if len(operation[INPUTS]) != len(operation[SIGS]):
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       "all inputs should have signatures")
        return TokenReqHandler._public_inputs_validator.validate(operation[INPUTS])

    @staticmethod
    def _operation_address_validate(request: Request):
        operation = request.operation
        if ADDRESS not in operation:
            error = '{} needs to be provided'.format(ADDRESS)
        else:
            error = TokenReqHandler._public_output_validator.inner_field_type.public_address_field.validate(operation[ADDRESS])
        if error:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId, error)

    def _reqToTxn(self, req: Request):
        if req.operation[TXN_TYPE] == XFER_PUBLIC:
            sigs = req.operation.pop(SIGS)
        txn = reqToTxn(req)
        if req.operation[TXN_TYPE] == XFER_PUBLIC:
            sigs = [(i[0], s) for i, s in zip(req.operation[INPUTS], sigs)]
            add_sigs_to_txn(txn, sigs, sig_type=ED25519)
        return txn

    def doStaticValidation(self, request: Request):
        operation = request.operation
        if operation[TXN_TYPE] in (MINT_PUBLIC, XFER_PUBLIC, GET_UTXO):
            # This is the python way of doing a switch statement.
            # It seems cleaner than a stack of if/elif/else
            # TODO: This should be moved outside the function, should be created once.
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
        typ = get_type(txn)
        if typ == MINT_PUBLIC:
            payload = get_payload_data(txn)
            seq_no = get_seq_no(txn)
            for addr, amount in payload[OUTPUTS]:
                self._add_new_output(Output(addr, seq_no, amount),
                                     is_committed=is_committed)
        if typ == XFER_PUBLIC:
            payload = get_payload_data(txn)
            for addr, seq_no in payload[INPUTS]:
                self._spend_input(addr, seq_no, is_committed=is_committed)
            for addr, amount in payload[OUTPUTS]:
                seq_no = get_seq_no(txn)
                self._add_new_output(Output(addr, seq_no, amount),
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

        outputs = []
        for k, v in rv.items():
            addr, seq_no = self.parse_state_key(k.decode())
            amount = rlp_decode(v)[0]
            if not amount:
                continue
            outputs.append(Output(addr, int(seq_no), int(amount)))

        result = {f.IDENTIFIER.nm: request.identifier,
                  f.REQ_ID.nm: request.reqId, OUTPUTS: outputs}
        if proof:
            result[STATE_PROOF] = proof

        result.update(request.operation)
        return result

    def _sum_inputs(self, inputs: Iterable, is_committed=False) -> int:
        return self.sum_inputs(self.utxo_cache, inputs,
                               is_committed=is_committed)

    @staticmethod
    def create_state_key(address: str, seq_no: int) -> bytes:
        return ':'.join([address, str(seq_no)]).encode()

    @staticmethod
    def parse_state_key(key: str) -> List[str]:
        return key.split(':')

    @staticmethod
    def sum_inputs(utxo_cache: UTXOCache, inputs: Iterable,
                   is_committed=False) -> int:
        output_val = 0
        for addr, seq_no in inputs:
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
