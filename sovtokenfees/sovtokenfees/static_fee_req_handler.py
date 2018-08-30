from common.serializers.serialization import proof_nodes_serializer, \
    state_roots_serializer  # , txn_root_serializer
# TODO fix that once PR to plenum is merged (https://github.com/hyperledger/indy-plenum/pull/767/)
from common.serializers.base58_serializer import Base58Serializer
from sovtoken.util import validate_multi_sig_txn
from stp_core.common.log import getlogger

txn_root_serializer = Base58Serializer()

from common.serializers.json_serializer import JsonSerializer
from plenum.common.constants import TXN_TYPE, TRUSTEE, ROOT_HASH, PROOF_NODES, \
    STATE_PROOF, MULTI_SIGNATURE, TXN_PAYLOAD, TXN_PAYLOAD_DATA
from plenum.common.exceptions import UnauthorizedClientRequest, \
    InvalidClientRequest, InvalidClientMessageException
from plenum.common.request import Request
from plenum.common.txn_util import reqToTxn, get_type, get_payload_data, get_seq_no, \
    get_req_id
from plenum.common.types import f, OPERATION
from sovtokenfees.constants import SET_FEES, GET_FEES, FEES, REF, FEE_TXN
from sovtokenfees.fee_req_handler import FeeReqHandler
from sovtokenfees.messages.fields import FeesStructureField
from sovtoken.constants import INPUTS, OUTPUTS, \
    XFER_PUBLIC, AMOUNT, ADDRESS, SEQNO
from sovtoken.token_req_handler import TokenReqHandler
from sovtoken.types import Output
from sovtoken.exceptions import InsufficientFundsError, ExtraFundsError, \
    UTXOError, InvalidFundsError
from state.trie.pruning_trie import rlp_decode


logger = getlogger()


class StaticFeesReqHandler(FeeReqHandler):
    valid_txn_types = {SET_FEES, GET_FEES, FEE_TXN}
    write_types = {SET_FEES, FEE_TXN}
    query_types = {GET_FEES, }
    _fees_validator = FeesStructureField()
    MinSendersForFees = 3
    fees_state_key = b'fees'
    state_serializer = JsonSerializer()

    def __init__(self, ledger, state, token_ledger, token_state, utxo_cache,
                 domain_state, bls_store):
        super().__init__(ledger, state)
        self.token_ledger = token_ledger
        self.token_state = token_state
        self.utxo_cache = utxo_cache
        self.domain_state = domain_state
        self.bls_store = bls_store

        # In-memory map of sovtokenfees, changes on SET_FEES txns
        self.fees = self._get_fees(is_committed=True)

        self.query_handlers = {
            GET_FEES: self.get_fees,
        }

        # Tracks count of transactions paying sovtokenfees while a batch is being
        # processed. Reset to zero once a batch is created (not committed)
        self.fee_txns_in_current_batch = 0
        # Tracks amount of deducted sovtokenfees for a transaction
        self.deducted_fees = {}
        # Since inputs are spent in XFER. FIND A BETTER SOLUTION
        self.deducted_fees_xfer = {}
        # Tracks txn and state root for each batch with at least 1 transaction
        # paying sovtokenfees
        self.uncommitted_state_roots_for_batches = []

    @staticmethod
    def has_fees(request) -> bool:
        return hasattr(request, FEES) and isinstance(request.fees, list) \
               and len(request.fees) > 0 and isinstance(request.fees[0], list) \
               and len(request.fees[0]) > 0

    @staticmethod
    def get_change_for_fees(request) -> list:
        return request.fees[1] if len(request.fees) >= 2 else []

    @staticmethod
    def get_ref_for_txn_fees(ledger_id, seq_no):
        return '{}:{}'.format(ledger_id, seq_no)

    def get_txn_fees(self, request) -> int:
        return self.fees.get(request.operation[TXN_TYPE], 0)

    def can_pay_fees(self, request):
        required_fees = self.get_txn_fees(request)
        if self.has_fees(request) and not required_fees:
            raise InvalidClientMessageException(getattr(request, f.IDENTIFIER.nm, None),
                                                getattr(request, f.REQ_ID.nm, None),
                                                'Fees are not allowed for this txn type')
        if request.operation[TXN_TYPE] == XFER_PUBLIC:
            # Fees in XFER_PUBLIC is part of operation[INPUTS]
            self._get_deducted_fees_xfer(request, required_fees)
            self.deducted_fees_xfer[request.key] = required_fees
        elif required_fees:
            self._get_deducted_fees_non_xfer(request, required_fees)

    # TODO: Fix this to match signature of `FeeReqHandler` and extract
    # the params from `kwargs`
    def deduct_fees(self, request, cons_time, ledger_id, seq_no, txn):
        txn_type = request.operation[TXN_TYPE]
        fees_key = "{}#{}".format(txn_type, seq_no)
        if txn_type == XFER_PUBLIC:
            if request.key in self.deducted_fees_xfer:
                self.deducted_fees[fees_key] = self.deducted_fees_xfer.pop(request.key)
        else:
            if self.has_fees(request):
                inputs, outputs, signatures = getattr(request, f.FEES.nm)
                # This is correct since FEES is changed from config ledger whose
                # transactions have no fees
                fees = self.get_txn_fees(request)
                sigs = {i[ADDRESS]: s for i, s in zip(inputs, signatures)}
                txn = {
                    OPERATION: {
                        TXN_TYPE: FEE_TXN,
                        INPUTS: inputs,
                        OUTPUTS: outputs,
                        REF: self.get_ref_for_txn_fees(ledger_id, seq_no),
                        FEES: fees,
                    },
                    f.SIGS.nm: sigs,
                    f.REQ_ID.nm: get_req_id(txn),
                    f.PROTOCOL_VERSION.nm: 2,
                }
                txn = reqToTxn(txn)
                self.token_ledger.append_txns_metadata([txn], txn_time=cons_time)
                _, txns = self.token_ledger.appendTxns([TokenReqHandler.transform_txn_for_ledger(txn)])
                self.updateState(txns)
                self.fee_txns_in_current_batch += 1
                self.deducted_fees[fees_key] = fees
                return txn

    def doStaticValidation(self, request: Request):
        operation = request.operation
        if operation[TXN_TYPE] in (SET_FEES, GET_FEES):
            error = ''
            if operation[TXN_TYPE] == SET_FEES:
                error = self._fees_validator.validate(operation.get(FEES))
            if error:
                raise InvalidClientRequest(request.identifier, request.reqId,
                                           error)
        else:
            super().doStaticValidation(request)

    def validate(self, req: Request):
        operation = req.operation
        if operation[TXN_TYPE] == SET_FEES:
            validate_multi_sig_txn(req, TRUSTEE, self.domain_state, self.MinSendersForFees)
        else:
            super().validate(req)

    def get_query_response(self, request: Request):
        return self.query_handlers[request.operation[TXN_TYPE]](request)

    def updateState(self, txns, isCommitted=False):
        for txn in txns:
            self._update_state_with_single_txn(txn, is_committed=isCommitted)

    def get_fees(self, request: Request):
        fees, proof = self._get_fees(is_committed=True, with_proof=True)
        result = {f.IDENTIFIER.nm: request.identifier,
                  f.REQ_ID.nm: request.reqId, FEES: fees}
        if proof:
            result[STATE_PROOF] = proof
        result.update(request.operation)
        return result

    def post_batch_created(self, ledger_id, state_root):
        if self.fee_txns_in_current_batch > 0:
            state_root = self.token_state.headHash
            txn_root = self.token_ledger.uncommittedRootHash
            self.uncommitted_state_roots_for_batches.append((txn_root, state_root))
            TokenReqHandler.on_batch_created(self.utxo_cache, state_root)
            self.fee_txns_in_current_batch = 0

    def post_batch_rejected(self, ledger_id):
        if self.fee_txns_in_current_batch > 0:
            TokenReqHandler.on_batch_rejected(self.utxo_cache)
            self.fee_txns_in_current_batch = 0

    def post_batch_committed(self, ledger_id, pp_time, committed_txns,
                             state_root, txn_root):
        committed_seq_nos_with_fees = [get_seq_no(t) for t in committed_txns
                                       if "{}#{}".format(get_type(t), get_seq_no(t)) in self.deducted_fees
                                       and get_type(t) != XFER_PUBLIC
                                       ]
        if len(committed_seq_nos_with_fees) > 0:
            txn_root, state_root = self.uncommitted_state_roots_for_batches.pop(0)
            r = TokenReqHandler.__commit__(self.utxo_cache, self.token_ledger,
                                           self.token_state,
                                           len(committed_seq_nos_with_fees),
                                           state_root, txn_root_serializer.serialize(txn_root),
                                           pp_time)
            i = 0
            for txn in committed_txns:
                if get_seq_no(txn) in committed_seq_nos_with_fees:
                    txn[FEES] = r[i]
                    i += 1

    def _get_deducted_fees_xfer(self, request, required_fees):
        try:
            sum_inputs = TokenReqHandler.sum_inputs(self.utxo_cache,
                                                    request,
                                                    is_committed=False)

            sum_outputs = TokenReqHandler.sum_outputs(request)
        except InvalidClientMessageException as ex:
            raise ex
        except Exception as ex:
                error = 'Exception {} while processing inputs/outputs'.format(ex)
                raise UnauthorizedClientRequest(request.identifier, request.reqId, error)
        else:
            expected_amount = sum_outputs + required_fees
            TokenReqHandler.validate_given_inputs_outputs(sum_inputs, sum_outputs,
                                                          expected_amount, request,
                                                          'fees: {}'.format(required_fees))

    def _get_deducted_fees_non_xfer(self, request, required_fees):
        if not self.has_fees(request):
            error = 'fees not present or improperly formed'
            raise UnauthorizedClientRequest(request.identifier, request.reqId, error)
        else:
            try:
                sum_inputs = self.utxo_cache.sum_inputs(request.fees[0], is_committed=False)
            except UTXOError as ex:
                raise InvalidFundsError(request.identifier, request.reqId, "{}".format(ex))
            else:
                change_amount = sum([a[AMOUNT] for a in self.get_change_for_fees(request)])
                expected_amount = change_amount + required_fees
                TokenReqHandler.validate_given_inputs_outputs(sum_inputs, change_amount,
                                                              expected_amount, request,
                                                              'fees: {}'.format(required_fees))

    def _get_fees(self, is_committed=False, with_proof=False):
        fees = {}
        proof = None
        try:
            if with_proof:
                proof, serz = self.state.generate_state_proof(self.fees_state_key,
                                                              serialize=True,
                                                              get_value=True)
                if serz:
                    serz = rlp_decode(serz)[0]
                root_hash = self.state.committedHeadHash if is_committed else self.state.headHash
                encoded_root_hash = state_roots_serializer.serialize(bytes(root_hash))
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
            else:
                serz = self.state.get(self.fees_state_key,
                                      isCommitted=is_committed)
            if serz:
                fees = self.state_serializer.deserialize(serz)
        except KeyError:
            pass
        if with_proof:
            return fees, proof
        return fees

    def _update_state_with_single_txn(self, txn, is_committed=False):
        typ = get_type(txn)
        if typ == SET_FEES:
            payload = get_payload_data(txn)
            existing_fees = self._get_fees(is_committed=is_committed)
            existing_fees.update(payload[FEES])
            val = self.state_serializer.serialize(existing_fees)
            self.state.set(self.fees_state_key, val)
            self.fees = existing_fees
        elif typ == FEE_TXN:
            for utxo in txn[TXN_PAYLOAD][TXN_PAYLOAD_DATA][INPUTS]:
                TokenReqHandler.spend_input(
                    state=self.token_state,
                    utxo_cache=self.utxo_cache,
                    address=utxo[ADDRESS],
                    seq_no=utxo[SEQNO],
                    is_committed=is_committed
                )
            seq_no = get_seq_no(txn)
            for output in txn[TXN_PAYLOAD][TXN_PAYLOAD_DATA][OUTPUTS]:
                TokenReqHandler.add_new_output(
                    state=self.token_state,
                    utxo_cache=self.utxo_cache,
                    output=Output(
                        output[ADDRESS],
                        seq_no,
                        output[AMOUNT]),
                    is_committed=is_committed)
        else:
            logger.warning('Unknown type {} found while updating '
                           'state with txn {}'.format(typ, txn))

    @staticmethod
    def _handle_incorrect_funds(sum_inputs, sum_outputs, expected_amount, required_fees, request):
        if sum_inputs < expected_amount:
            error = 'Insufficient funds, sum of inputs is {} ' \
                    'but required is {} (sum of outputs: {}, ' \
                    'fees: {})'.format(sum_inputs, expected_amount, sum_outputs, required_fees)
            raise InsufficientFundsError(request.identifier, request.reqId, error)
        if sum_inputs > expected_amount:
            error = 'Extra funds, sum of inputs is {} ' \
                    'but required is {} (sum of outputs: {}, ' \
                    'fees: {})'.format(sum_inputs, expected_amount, sum_outputs, required_fees)
            raise ExtraFundsError(request.identifier, request.reqId, error)

    @staticmethod
    def transform_txn_for_ledger(txn):
        """
        Some transactions need to be updated before they can be stored in the
        ledger
        """
        return txn
