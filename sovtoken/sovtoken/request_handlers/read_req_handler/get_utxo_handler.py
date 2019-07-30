try:
    import ujson as json
except ImportError:
    import json
from copy import deepcopy

from sovtoken import TokenTransactions
from sovtoken.constants import ADDRESS, OUTPUTS, TOKEN_LEDGER_ID, NEXT_SEQNO, UTXO_LIMIT, FROM_SEQNO
from sovtoken.messages.txn_validator import txt_get_utxo_validate
from sovtoken.request_handlers.token_utils import TokenStaticHelper
from sovtoken.types import Output
from sovtoken.util import SortedItems

from sovtokenfees.serializers import state_roots_serializer, proof_nodes_serializer
from plenum.common.constants import MULTI_SIGNATURE, ROOT_HASH, PROOF_NODES, STATE_PROOF
from plenum.common.exceptions import InvalidClientRequest
from plenum.common.request import Request
from plenum.common.types import f
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.handler_interfaces.read_request_handler import ReadRequestHandler
from state.trie.pruning_trie import rlp_decode


class GetUtxoHandler(ReadRequestHandler):
    def __init__(self, database_manager: DatabaseManager, msg_limit):
        super().__init__(database_manager, TokenTransactions.GET_UTXO.value, TOKEN_LEDGER_ID)
        self._msg_limit = msg_limit

    def static_validation(self, request: Request):
        error = txt_get_utxo_validate(request)

        if error:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       error)

    @staticmethod
    def create_state_key(address: str, seq_no: int) -> bytes:
        return TokenStaticHelper.create_state_key(address=address, seq_no=seq_no)

    def get_result(self, request: Request):
        address = request.operation[ADDRESS]
        from_seqno = request.operation.get(FROM_SEQNO)
        encoded_root_hash = state_roots_serializer.serialize(
            bytes(self.state.committedHeadHash))
        proof, rv = self.state.generate_state_proof_for_keys_with_prefix(address,
                                                                         serialize=True,
                                                                         get_value=True)
        multi_sig = self.database_manager.bls_store.get(encoded_root_hash)
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
            addr, seq_no = TokenStaticHelper.parse_state_key(k.decode())
            amount = rlp_decode(v)[0]
            if not amount:
                continue
            outputs.add(Output(addr, int(seq_no), int(amount)))

        utxos = outputs.sorted_list
        next_seqno = None
        if from_seqno:
            idx = next((idx for utxo, idx in zip(utxos, range(len(utxos))) if utxo.seqNo >= from_seqno), None)
            if idx:
                utxos = utxos[idx:]
            else:
                utxos = []
        if len(utxos) > UTXO_LIMIT:
            next_seqno = utxos[UTXO_LIMIT].seqNo
            utxos = utxos[:UTXO_LIMIT]

        result = {f.IDENTIFIER.nm: request.identifier,
                  f.REQ_ID.nm: request.reqId, OUTPUTS: utxos}

        result.update(request.operation)
        if next_seqno:
            result[NEXT_SEQNO] = next_seqno
        if proof:
            res_sub = deepcopy(result)
            res_sub[STATE_PROOF] = proof
            if len(json.dumps(res_sub)) <= self._msg_limit:
                result = res_sub
        return result
