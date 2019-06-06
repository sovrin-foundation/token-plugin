import json

import pytest
from indy_node.test.request_handlers.helper import get_fake_ledger
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.utxo_cache import UTXOCache
from indy.payment import create_payment_address
from indy.wallet import create_wallet, open_wallet, close_wallet, delete_wallet

from common.serializers import serialization
from plenum.bls.bls_store import BlsStore
from plenum.common.constants import KeyValueStorageType
from plenum.common.util import randomString
from plenum.server.database_manager import DatabaseManager
from state.pruning_state import PruningState
from storage.helper import initKeyValueStorage


@pytest.fixture(scope="module")
def bls_store():
    return BlsStore(key_value_type=KeyValueStorageType.Memory,
                    data_location=None,
                    key_value_storage_name="BlsInMemoryStore",
                    serializer=serialization.multi_sig_store_serializer)


@pytest.fixture(scope="module")
def db_manager(tconf):
    db_manager = DatabaseManager()
    storage = initKeyValueStorage(KeyValueStorageType.Memory,
                                  None,
                                  "tokenInMemoryStore",
                                  txn_serializer=serialization.multi_sig_store_serializer)
    ledger = get_fake_ledger()
    ledger.commitTxns = lambda x: (None, [])
    ledger.root_hash = 1
    db_manager.register_new_database(TOKEN_LEDGER_ID, ledger, PruningState(storage))
    return db_manager


@pytest.yield_fixture(scope="module")
def utxo_cache(db_manager):
    cache = UTXOCache(initKeyValueStorage(
        KeyValueStorageType.Memory, None, "utxoInMemoryStore"))
    db_manager.register_new_store("utxo_cache", cache)
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

