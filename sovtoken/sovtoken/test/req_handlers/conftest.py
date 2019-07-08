import json

import pytest
from base58 import b58decode
from sovtoken.constants import UTXO_CACHE_LABEL
from sovtokenfees.static_fee_req_handler import txn_root_serializer

from indy_node.test.request_handlers.helper import get_fake_ledger
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.utxo_cache import UTXOCache
from indy.payment import create_payment_address
from indy.wallet import create_wallet, open_wallet, close_wallet, delete_wallet

from common.serializers import serialization
from plenum.common.constants import KeyValueStorageType, BLS_LABEL
from plenum.common.txn_util import append_txn_metadata
from plenum.common.util import randomString
from plenum.server.database_manager import DatabaseManager
from plenum.test.testing_utils import FakeSomething
from state.pruning_state import PruningState
from storage.helper import initKeyValueStorage

FAKE_UNCOMMITTED_ROOT_HASH = b58decode("1".encode())
FAKE_COMMITTED_ROOT_HASH = b58decode("1".encode())


@pytest.fixture(scope="module")
def bls_store(db_manager):
    multi_sigs = FakeSomething()
    multi_sigs.as_dict = lambda: {"a": "b"}
    bls = FakeSomething()
    bls.get = lambda _: multi_sigs
    db_manager.register_new_store(BLS_LABEL, bls)
    return bls


@pytest.fixture(scope="module")
def db_manager(tconf):
    db_manager = DatabaseManager()
    storage = initKeyValueStorage(KeyValueStorageType.Memory,
                                  None,
                                  "tokenInMemoryStore",
                                  txn_serializer=serialization.multi_sig_store_serializer)
    ledger = get_fake_ledger()
    ledger.commitTxns = lambda x: (None, [1])
    ledger.root_hash = txn_root_serializer.serialize("1")
    ledger.uncommitted_root_hash = "1"
    ledger.uncommitted_size = 1
    ledger.size = 0
    ledger.discardTxns = lambda x: None
    ledger.committed_root_hash = "-1"
    ledger.append_txns_metadata = lambda txns, txn_time: [append_txn_metadata(txn, 2, txn_time, 2) for txn in txns]
    ledger.appendTxns = lambda x: (None, x)
    db_manager.register_new_database(TOKEN_LEDGER_ID, ledger, PruningState(storage))
    return db_manager


@pytest.yield_fixture(scope="module")
def utxo_cache(db_manager):
    cache = UTXOCache(initKeyValueStorage(
        KeyValueStorageType.Memory, None, "utxoInMemoryStore"))
    db_manager.register_new_store(UTXO_CACHE_LABEL, cache)
    yield cache
    if cache.un_committed:
        cache.reject_batch()


@pytest.fixture(scope="module")
def payment_address(libsovtoken, looper, wallet):
    payment_address_future = create_payment_address(wallet, "sov", "{}")
    payment_address = looper.loop.run_until_complete(payment_address_future)
    return payment_address


@pytest.fixture(scope="module")
def payment_address_2(libsovtoken, looper, wallet):
    payment_address_future = create_payment_address(wallet, "sov", "{}")
    payment_address = looper.loop.run_until_complete(payment_address_future)
    return payment_address


@pytest.yield_fixture(scope="module")
def wallet(looper):
    wallet_name = randomString()

    create_wallet_future = create_wallet(json.dumps({"id": wallet_name}), json.dumps({"key": "1"}))
    looper.loop.run_until_complete(create_wallet_future)

    open_wallet_future = open_wallet(json.dumps({"id": wallet_name}), json.dumps({"key": "1"}))
    wallet_handle = looper.loop.run_until_complete(open_wallet_future)

    yield wallet_handle

    close_wallet_future = close_wallet(wallet_handle)
    looper.loop.run_until_complete(close_wallet_future)

    delete_wallet_future = delete_wallet(json.dumps({"id": wallet_name}), json.dumps({"key": "1"}))
    looper.loop.run_until_complete(delete_wallet_future)
