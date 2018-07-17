import pytest
from sovtokenfees.static_fee_req_handler import \
    StaticFeesReqHandler

from common.serializers.serialization import state_roots_serializer

from state.db.persistent_db import PersistentDB

from state.trie.pruning_trie import Trie, rlp_encode
from storage.kv_in_memory import KeyValueStorageInMemory

from plenum.common.constants import NYM, STEWARD, STATE_PROOF, PROOF_NODES, \
    ROOT_HASH
from plenum.common.exceptions import RequestNackedException, \
    RequestRejectedException
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import get_fees_from_ledger, \
    check_fee_req_handler_in_memory_map_updated, send_set_fees, set_fees, \
    send_get_fees
from sovtoken.constants import XFER_PUBLIC
from sovtoken.test.helper import decode_proof, do_public_minting
from plenum.test.conftest import get_data_for_role
from sovtoken.test.conftest import build_wallets_from_data


def test_get_fees_when_no_fees_set(looper, nodeSetWithIntegratedTokenPlugin,
                                   sdk_wallet_client, sdk_pool_handle):
    assert get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle) == {}
    check_fee_req_handler_in_memory_map_updated(nodeSetWithIntegratedTokenPlugin, {})


def test_trustee_set_invalid_fees(looper, nodeSetWithIntegratedTokenPlugin,
                                  sdk_wallet_client, sdk_pool_handle,
                                  trustee_wallets):
    """
    Fees cannot be negative
    """
    fees = {
        NYM: -1,
        XFER_PUBLIC: 2
    }
    with pytest.raises(RequestNackedException):
        send_set_fees(looper, trustee_wallets, fees, sdk_pool_handle)
    assert get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle) == {}


def test_non_trustee_set_fees(looper, nodeSetWithIntegratedTokenPlugin,
                              sdk_wallet_client, sdk_pool_handle, poolTxnData):
    """
    Only trustees can change the sovtokenfees
    """
    fees = {
        NYM: 1,
        XFER_PUBLIC: 2
    }
    steward_data = get_data_for_role(poolTxnData, STEWARD)
    steward_wallets = build_wallets_from_data(steward_data)
    with pytest.raises(RequestRejectedException):
        send_set_fees(looper, steward_wallets, fees, sdk_pool_handle)
    assert get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle) == {}


@pytest.fixture(scope="module")
def fees_set(looper, nodeSetWithIntegratedTokenPlugin, sdk_pool_handle,
             trustee_wallets, fees):
    return set_fees(looper, trustee_wallets, fees, sdk_pool_handle)


def test_trustee_set_valid_fees(fees_set, nodeSetWithIntegratedTokenPlugin,
                                fees):
    """
    Set a valid sovtokenfees
    """
    check_fee_req_handler_in_memory_map_updated(
        nodeSetWithIntegratedTokenPlugin, fees)


def test_get_fees(fees_set, looper, nodeSetWithIntegratedTokenPlugin,
                  sdk_wallet_client, sdk_pool_handle, fees):
    """
    Get the sovtokenfees from the ledger
    """
    assert get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle) == fees


def test_change_fees(fees_set, looper, nodeSetWithIntegratedTokenPlugin,
                     sdk_wallet_client, sdk_pool_handle, trustee_wallets, fees):
    """
    Change the sovtokenfees on the ledger and check that sovtokenfees has changed
    """
    updated_fees = {**fees, NYM: 10}
    set_fees(looper, trustee_wallets, updated_fees, sdk_pool_handle)
    new_fees = get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle)
    assert new_fees == updated_fees
    assert new_fees != fees
    check_fee_req_handler_in_memory_map_updated(nodeSetWithIntegratedTokenPlugin,
                                                updated_fees)


def test_get_fees_with_proof(fees_set, looper, nodeSetWithIntegratedTokenPlugin,
                             sdk_wallet_client, sdk_pool_handle, fees):
    """
    Get the sovtokenfees from the ledger
    """
    res = send_get_fees(looper, sdk_wallet_client, sdk_pool_handle)
    fees = res[FEES]
    state_proof = res[STATE_PROOF]
    assert state_proof
    proof_nodes = decode_proof(res[STATE_PROOF][PROOF_NODES])
    client_trie = Trie(PersistentDB(KeyValueStorageInMemory()))
    fees = rlp_encode([StaticFeesReqHandler.state_serializer.serialize(fees)])
    assert client_trie.verify_spv_proof(
        state_roots_serializer.deserialize(res[STATE_PROOF][ROOT_HASH]),
        StaticFeesReqHandler.fees_state_key, fees, proof_nodes)


def test_mint_after_set_fees(fees_set, looper, nodeSetWithIntegratedTokenPlugin,
                             trustee_wallets, SF_address, seller_address,
                             sdk_pool_handle):
    # Try another minting after setting fees
    total_mint = 100
    sf_master_gets = 60
    do_public_minting(looper, trustee_wallets, sdk_pool_handle, total_mint,
                      sf_master_gets, SF_address, seller_address)
