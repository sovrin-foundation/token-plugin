from sovtoken.request_handlers.token_utils import TokenStaticHelper
from sovtoken.request_handlers.write_request_handler.xfer_handler import XferHandler

from storage.kv_in_memory import KeyValueStorageInMemory

from state.db.persistent_db import PersistentDB

from common.serializers.serialization import state_roots_serializer

from plenum.common.constants import STATE_PROOF, PROOF_NODES, ROOT_HASH
from sovtoken.constants import OUTPUTS
from sovtoken.util import update_token_wallet_with_result

from sovtoken.test.helper import send_get_utxo, send_xfer, \
    decode_proof
from state.trie.pruning_trie import Trie, rlp_encode


def test_state_proof(public_minting, looper,  # noqa
                     sdk_pool_handle, sdk_wallet_client,
                     seller_token_wallet, seller_address,
                     user1_token_wallet, user1_address):
    res = send_get_utxo(looper, seller_address, sdk_wallet_client, sdk_pool_handle)
    update_token_wallet_with_result(seller_token_wallet, res)

    # Do 20 XFER txns
    for _ in range(20):
        utxos = [_ for lst in
                 seller_token_wallet.get_all_wallet_utxos().values()
                 for _ in lst]
        seq_no, amount = utxos[0]
        inputs = [[seller_token_wallet, seller_address, seq_no]]
        outputs = [{"address": user1_address, "amount": 1}, {"address": seller_address, "amount": amount - 1}]
        res = send_xfer(looper, inputs, outputs, sdk_pool_handle)
        update_token_wallet_with_result(seller_token_wallet, res)
        res = send_get_utxo(looper, seller_address, sdk_wallet_client,
                            sdk_pool_handle)
        update_token_wallet_with_result(seller_token_wallet, res)
        res = send_get_utxo(looper, user1_address, sdk_wallet_client,
                            sdk_pool_handle)
        update_token_wallet_with_result(user1_token_wallet, res)

    res = send_get_utxo(looper, user1_address, sdk_wallet_client,
                        sdk_pool_handle)

    # Check presence of state proof
    assert res[STATE_PROOF]
    encoded = {}
    outputs = res[OUTPUTS]
    for out in outputs:
        state_key = TokenStaticHelper.create_state_key(out["address"], out["seqNo"])
        encoded[state_key] = rlp_encode([str(out["amount"])])
    proof_nodes = decode_proof(res[STATE_PROOF][PROOF_NODES])
    client_trie = Trie(PersistentDB(KeyValueStorageInMemory()))
    assert client_trie.verify_spv_proof_multi(
        state_roots_serializer.deserialize(res[STATE_PROOF][ROOT_HASH]),
        encoded, proof_nodes)
