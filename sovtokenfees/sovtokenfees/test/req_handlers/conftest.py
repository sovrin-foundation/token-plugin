import json

import pytest
from common.serializers.json_serializer import JsonSerializer
from sovtoken.constants import UTXO_CACHE_LABEL
from sovtoken.utxo_cache import UTXOCache
from sovtokenfees.req_handlers.fees_utils import BatchFeesTracker

from indy_common.constants import CONFIG_LEDGER_ID

from indy_node.test.request_handlers.helper import get_fake_ledger
from sovtoken.test.req_handlers.conftest import db_manager as dbm

from common.serializers import serialization
from plenum.common.constants import KeyValueStorageType, BLS_LABEL
from plenum.test.testing_utils import FakeSomething
from state.pruning_state import PruningState
from storage.helper import initKeyValueStorage

in_memory_serializer = JsonSerializer()


@pytest.fixture(scope="module")
def db_manager(dbm):
    _db_manager = dbm
    storage = initKeyValueStorage(KeyValueStorageType.Memory,
                                  None,
                                  "configInMemoryStore",
                                  txn_serializer=in_memory_serializer)
    ledger = get_fake_ledger()
    _db_manager.register_new_database(CONFIG_LEDGER_ID, ledger, PruningState(storage))
    return _db_manager


@pytest.fixture(scope="module")
def bls_store(db_manager):
    multi_sigs = FakeSomething()
    multi_sigs.as_dict = lambda: {"a": "b"}
    bls = FakeSomething()
    bls.get = lambda _: multi_sigs
    db_manager.register_new_store(BLS_LABEL, bls)
    return bls


@pytest.fixture(scope="module")
def fees():
    return json.dumps({"nym_alias": 1, "attrib_alias": 2})


@pytest.fixture(scope="module")
def fees_tracker():
    return BatchFeesTracker()
