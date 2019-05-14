from common.serializers.serialization import proof_nodes_serializer, \
    state_roots_serializer
from common.serializers.base58_serializer import Base58Serializer

from indy_common.authorize.auth_actions import AuthActionEdit
from stp_core.common.log import getlogger
from plenum.server.node import Node
from plenum.common.ledger_uncommitted_tracker import LedgerUncommittedTracker

txn_root_serializer = Base58Serializer()

from common.serializers.json_serializer import JsonSerializer
from plenum.common.constants import TXN_TYPE, TRUSTEE, ROOT_HASH, PROOF_NODES, \
    STATE_PROOF, MULTI_SIGNATURE, TXN_PAYLOAD, TXN_PAYLOAD_DATA, ALIAS
from plenum.common.exceptions import UnauthorizedClientRequest, \
    InvalidClientRequest, InvalidClientMessageException
from plenum.common.request import Request
from plenum.common.txn_util import reqToTxn, get_type, get_payload_data, get_seq_no, \
    get_req_id
from plenum.common.types import f, OPERATION
from sovtokenfees.constants import SET_FEES, GET_FEES, GET_FEE, FEES, REF, FEE_TXN, FEES_KEY_DELIMITER, \
    FEES_STATE_PREFIX, \
    FEES_KEY_FOR_ALL, FEE
from sovtokenfees.fee_req_handler import FeeReqHandler
from sovtokenfees.messages.fields import TxnFeesField, FEES_ALIAS, FEES_VALUE, SetFeesMsg, GetFeeMsg
from sovtoken.constants import INPUTS, OUTPUTS, \
    XFER_PUBLIC, AMOUNT, ADDRESS, SEQNO, TOKEN_LEDGER_ID
from sovtoken.token_req_handler import TokenReqHandler
from sovtoken.types import Output
from sovtoken.exceptions import InsufficientFundsError, ExtraFundsError, \
    UTXOError, InvalidFundsError
from state.trie.pruning_trie import rlp_decode


txn_root_serializer = Base58Serializer()
logger = getlogger()

class StaticFeesReqHandler(FeeReqHandler):
    write_types = FeeReqHandler.write_types.union({SET_FEES, FEE_TXN})
    query_types = FeeReqHandler.query_types.union({GET_FEES, GET_FEE})
    set_fees_validator_cls = SetFeesMsg
    get_fee_validator_cls = GetFeeMsg
    state_serializer = JsonSerializer()

    def __init__(self, ledger, state, token_ledger, token_state, utxo_cache,
                 domain_state, bls_store, node, write_req_validator, ts_store=None):

        super().__init__(ledger, state,
                         idrCache=node.idrCache,
                         upgrader=node.upgrader,
                         poolManager=node.poolManager,
                         poolCfg=node.poolCfg,
                         write_req_validator=node.write_req_validator,
                         ts_store=ts_store)

        self.token_ledger = token_ledger
        self.token_state = token_state
        self.utxo_cache = utxo_cache
        self.domain_state = domain_state
        self.bls_store = bls_store
        self.write_req_validator = write_req_validator

        self.query_handlers = {
            GET_FEES: self.get_fees,
            GET_FEE: self.get_fee,
        }

        # Tracks count of transactions paying sovtokenfees while a batch is being
        # processed. Reset to zero once a batch is created (not committed)
        self.fee_txns_in_current_batch = 0
        # Tracks amount of deducted sovtokenfees for a transaction
        self.deducted_fees = {}
        # Since inputs are spent in XFER. FIND A BETTER SOLUTION
        self.deducted_fees_xfer = {}
        self.token_tracker = LedgerUncommittedTracker(token_state.committedHeadHash,
                                                      token_ledger.uncommitted_root_hash,
                                                      token_ledger.size)

    @property
    def fees(self):
        return self._get_fees(is_committed=False)

    @staticmethod
    def has_fees(request) -> bool:
        return hasattr(request, FEES) and request.fees is not None

    @staticmethod
    def get_change_for_fees(request) -> list:
        return request.fees[1] if len(request.fees) >= 2 else []

    @staticmethod
    def get_ref_for_txn_fees(ledger_id, seq_no):
        return '{}:{}'.format(ledger_id, seq_no)

    @staticmethod
    def build_path_for_set_fees(alias=None):
        if alias:
            return FEES_KEY_DELIMITER.join([FEES_STATE_PREFIX, alias])
        return FEES_KEY_DELIMITER.join([FEES_STATE_PREFIX, FEES_KEY_FOR_ALL])

    def get_txn_fees(self, request) -> int:
        return self.fees.get(request.operation[TXN_TYPE], 0)

    def calculate_fees_from_req(self, request):
        inputs = request.fees[0]
        outputs = self.get_change_for_fees(request)
        try:
            sum_inputs = self.utxo_cache.sum_inputs(inputs, is_committed=False)
        except Exception as e:
            logger.error("Unexpected exception while sum_inputs calculating: {}".format(e))
            return 0

        sum_outputs = sum([a[AMOUNT] for a in outputs])
        return sum_inputs - sum_outputs


    def can_pay_fees(self, request, required_fees):

        if request.operation[TXN_TYPE] == XFER_PUBLIC:
            # Fees in XFER_PUBLIC is part of operation[INPUTS]
            inputs = request.operation[INPUTS]
            outputs = request.operation[OUTPUTS]
            self._validate_fees_can_pay(request, inputs, outputs, required_fees)
            self.deducted_fees_xfer[request.key] = required_fees
        else:
            inputs = request.fees[0]
            outputs = self.get_change_for_fees(request)
            self._validate_fees_can_pay(request, inputs, outputs, required_fees)

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
                fees = self.calculate_fees_from_req(request)
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
        if operation[TXN_TYPE] in (SET_FEES, GET_FEES, GET_FEE):
                try:
                    if operation[TXN_TYPE] == SET_FEES:
                        self.set_fees_validator_cls(**request.operation)
                    elif operation[TXN_TYPE] == GET_FEE:
                        self.get_fee_validator_cls(**request.operation)
                except TypeError as exc:
                    raise InvalidClientRequest(request.identifier,
                                               request.reqId,
                                               exc)
        else:
            super().doStaticValidation(request)

    def validate(self, request: Request):
        operation = request.operation
        if operation[TXN_TYPE] == SET_FEES:
            return self.write_req_validator.validate(request,
                                                     [AuthActionEdit(txn_type=SET_FEES,
                                                                     field="*",
                                                                     old_value="*",
                                                                     new_value="*")])
        else:
            super().validate(request)

    def get_query_response(self, request: Request):
        return self.query_handlers[request.operation[TXN_TYPE]](request)

    def updateState(self, txns, isCommitted=False):
        for txn in txns:
            self._update_state_with_single_txn(txn, is_committed=isCommitted)
        super().updateState(txns, isCommitted=isCommitted)

    def get_fees(self, request: Request):
        fees, proof = self._get_fees(is_committed=True, with_proof=True)
        result = {f.IDENTIFIER.nm: request.identifier,
                  f.REQ_ID.nm: request.reqId, FEES: fees}
        if proof:
            result[STATE_PROOF] = proof
        result.update(request.operation)
        return result

    def get_fee(self, request: Request):
        alias = request.operation.get(ALIAS)
        fee, proof = self._get_fee(alias, is_committed=True, with_proof=True)
        if not fee:
            raise InvalidClientRequest(request.identifier, request.reqId,
                                       "'{}' not found.".format(alias))
        result = {f.IDENTIFIER.nm: request.identifier,
                  f.REQ_ID.nm: request.reqId, FEE: fee}
        if proof:
            result[STATE_PROOF] = proof
        result.update(request.operation)
        return result

    def post_batch_created(self, ledger_id, state_root):
        # it mean, that all tracker thins was done in onBatchCreated phase for TokenReqHandler
        self.token_tracker.apply_batch(self.token_state.headHash,
                                       self.token_ledger.uncommitted_root_hash,
                                       self.token_ledger.uncommitted_size)
        if ledger_id == TOKEN_LEDGER_ID:
            return
        if self.fee_txns_in_current_batch > 0:
            state_root = self.token_state.headHash
            TokenReqHandler.on_batch_created(self.utxo_cache, state_root)
            # ToDo: Needed investigation about affection of removing setting this var into 0
            self.fee_txns_in_current_batch = 0

    def post_batch_rejected(self, ledger_id):
        uncommitted_hash, uncommitted_txn_root, txn_count = self.token_tracker.reject_batch()
        if ledger_id == TOKEN_LEDGER_ID:
            # TODO: Need to improve this logic for case, when we got a XFER txn with fees
            # All of other txn with fees it's a 2 steps, "apply txn" and "apply fees"
            # But for XFER txn with fees we do only "apply fees with transfer too"
            return
        if txn_count == 0 or self.token_ledger.uncommitted_root_hash == uncommitted_txn_root or \
                self.token_state.headHash == uncommitted_hash:
            return 0
        self.token_state.revertToHead(uncommitted_hash)
        self.token_ledger.discardTxns(txn_count)
        count_reverted = TokenReqHandler.on_batch_rejected(self.utxo_cache)
        logger.info("Reverted {} txns with fees".format(count_reverted))

    def post_batch_committed(self, ledger_id, pp_time, committed_txns,
                             state_root, txn_root):
        # All changes will be tracked on TokenReqHandler side
        token_state_root, token_txn_root, _ = self.token_tracker.commit_batch()
        if ledger_id == TOKEN_LEDGER_ID:
            return
        committed_seq_nos_with_fees = [get_seq_no(t) for t in committed_txns
                                       if "{}#{}".format(get_type(t), get_seq_no(t)) in self.deducted_fees
                                       and get_type(t) != XFER_PUBLIC
                                       ]
        if len(committed_seq_nos_with_fees) > 0:
            r = TokenReqHandler.__commit__(self.utxo_cache, self.token_ledger,
                                           self.token_state,
                                           len(committed_seq_nos_with_fees),
                                           token_state_root, txn_root_serializer.serialize(token_txn_root),
                                           pp_time)
            i = 0
            for txn in committed_txns:
                if get_seq_no(txn) in committed_seq_nos_with_fees:
                    txn[FEES] = r[i]
                    i += 1
            self.fee_txns_in_current_batch = 0

    def _validate_fees_can_pay(self, request, inputs, outputs, required_fees):
        """
        Calculate and verify that inputs and outputs for fees can both be paid and change is properly specified

        This function ASSUMES that validation of the fees for the request has already been done.

        :param request:
        :param required_fees:
        :return:
        """

        try:
            sum_inputs = self.utxo_cache.sum_inputs(inputs, is_committed=False)
        except UTXOError as ex:
            raise InvalidFundsError(request.identifier, request.reqId, "{}".format(ex))
        except Exception as ex:
            error = 'Exception {} while processing inputs/outputs'.format(ex)
            raise UnauthorizedClientRequest(request.identifier, request.reqId, error)
        else:
            change_amount = sum([a[AMOUNT] for a in outputs])
            expected_amount = change_amount + required_fees
            TokenReqHandler.validate_given_inputs_outputs(
                sum_inputs,
                change_amount,
                expected_amount,
                request,
                'fees: {}'.format(required_fees)
            )

    def _get_fees(self, is_committed=False, with_proof=False):
        result = self._get_fee_from_state(is_committed=is_committed,
                                          with_proof=with_proof)
        if with_proof:
            fees, proof = result
            return fees, proof if fees is not None else ({}, None)
        else:
            return result if result is not None else {}

    def _get_fee(self, alias, is_committed=False, with_proof=False):
        return self._get_fee_from_state(fees_alias=alias,
                                        is_committed=is_committed,
                                        with_proof=with_proof)

    def _get_fee_from_state(self, fees_alias=None, is_committed=False, with_proof=False):
        fees = None
        proof = None
        try:
            fees_key = self.build_path_for_set_fees(alias=fees_alias)
            if with_proof:
                proof, serz = self.state.generate_state_proof(fees_key,
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
                serz = self.state.get(fees_key,
                                      isCommitted=is_committed)
            if serz:
                fees = self.state_serializer.deserialize(serz)
        except KeyError:
            pass
        if with_proof:
            return fees, proof
        return fees

    def _set_to_state(self, key, val):
        val = self.state_serializer.serialize(val)
        key = key.encode()
        self.state.set(key, val)

    def _update_state_with_single_txn(self, txn, is_committed=False):
        typ = get_type(txn)
        if typ == SET_FEES:
            payload = get_payload_data(txn)
            all_fees = payload.get(FEES)
            for fees_alias, fees_value in all_fees.items():
                self._set_to_state(self.build_path_for_set_fees(alias=fees_alias), fees_value)
            self._set_to_state(self.build_path_for_set_fees(), all_fees)

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

    @staticmethod
    def _handle_incorrect_funds(sum_inputs, sum_outputs, expected_amount, required_fees, request):
        if sum_inputs < expected_amount:
            error = 'Insufficient funds, sum of inputs is {} ' \
                    'but required is {} (sum of outputs: {}, ' \
                    'fees: {})'.format(sum_inputs, expected_amount, sum_outputs, required_fees)
            raise InsufficientFundsError(request.identifier, request.reqId, error)
        if sum_inputs > expected_amount:
            error = 'Extra funds, sum of inputs is {} ' \
                    'but required is: {} -- sum of outputs: {} ' \
                    '-- fees: {})'.format(sum_inputs, expected_amount, sum_outputs, required_fees)
            raise ExtraFundsError(request.identifier, request.reqId, error)

    @staticmethod
    def transform_txn_for_ledger(txn):
        """
        Some transactions need to be updated before they can be stored in the
        ledger
        """
        return txn

    def postCatchupCompleteClbk(self):
        self.token_tracker.set_last_committed(self.token_state.committedHeadHash,
                                              self.token_ledger.uncommitted_root_hash,
                                              self.token_ledger.size)
