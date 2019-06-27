import json
import pytest
from sovtoken.request_handlers.write_request_handler.xfer_handler import XferHandler

from common.serializers.serialization import proof_nodes_serializer

from plenum.common.constants import TXN_TYPE
from sovtoken.constants import MINT_PUBLIC, OUTPUTS, XFER_PUBLIC, \
    EXTRA, TOKEN_LEDGER_ID, GET_UTXO, ADDRESS, SIGS
from sovtoken.util import address_to_verkey
from plenum.test.helper import sdk_send_signed_requests, \
    sdk_get_and_check_replies, sdk_gen_request, sdk_sign_and_submit_req_obj
from state.trie.pruning_trie import Trie
from sovtoken.test.wallet import TokenWallet


def xfer_request(inputs, outputs, extra_data=None):
    payload = {
        TXN_TYPE: XFER_PUBLIC,
        OUTPUTS: outputs,
        EXTRA: extra_data,
        SIGS: []
    }
    wallet, address, seq_no = inputs[0]
    request = wallet.sign_using_output(address, seq_no, op=payload)
    for wallet, address, seq_no in inputs[1:]:
        wallet.sign_using_output(address, seq_no, request=request)
    # Setting the `_identifier` to conform to the `Request` structure
    request._identifier = address_to_verkey(address)
    return request


def send_xfer(looper, inputs, outputs, sdk_pool_handle, extra_data=None):
    request = xfer_request(inputs, outputs, extra_data)
    request = sdk_send_signed_requests(sdk_pool_handle,
                                       [json.dumps(request.as_dict), ])
    _, rep = sdk_get_and_check_replies(looper, request)[0]
    return rep['result']


def check_output_val_on_all_nodes(nodes, address, amount):
    for node in nodes:
        handler = next(h for h in node.write_manager.request_handlers[XFER_PUBLIC] if isinstance(h, XferHandler))
        assert int(amount) in [out.amount for out in
                               handler.utxo_cache.get_unspent_outputs(
                                   address, is_committed=True)]


def get_utxo_request(address, sender_did):
    op = {
        TXN_TYPE: GET_UTXO,
        ADDRESS: address,
    }
    request = sdk_gen_request(op, identifier=sender_did)
    return request


def send_get_utxo(looper, address, sdk_wallet_client, sdk_pool_handle):
    _, sender_did = sdk_wallet_client
    request = get_utxo_request(address, sender_did)
    req_resp_json = sdk_sign_and_submit_req_obj(looper, sdk_pool_handle,
                                                sdk_wallet_client, request)
    _, reply = sdk_get_and_check_replies(looper, [req_resp_json, ])[0]
    return reply['result']


def decode_proof(proof):
    proof = proof_nodes_serializer.deserialize(proof)
    return Trie.deserialize_proof(proof)


@pytest.fixture(scope="module")
def user1_token_wallet():
    return TokenWallet('user1')


@pytest.fixture(scope="module")
def user2_token_wallet():
    return TokenWallet('user2')


@pytest.fixture(scope="module")
def user3_token_wallet():
    return TokenWallet('user3')


@pytest.fixture(scope="module")
def user1_address(user1_token_wallet):
    seed = 'user1000000000000000000000000000'.encode()
    user1_token_wallet.add_new_address(seed=seed)
    return next(iter(user1_token_wallet.addresses.keys()))


@pytest.fixture(scope="module")
def user2_address(user2_token_wallet):
    seed = 'user2000000000000000000000000000'.encode()
    user2_token_wallet.add_new_address(seed=seed)
    return next(iter(user2_token_wallet.addresses.keys()))


@pytest.fixture(scope="module")
def user3_address(user3_token_wallet):
    seed = 'user3000000000000000000000000000'.encode()
    user3_token_wallet.add_new_address(seed=seed)
    return next(iter(user3_token_wallet.addresses.keys()))
