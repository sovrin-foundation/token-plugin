from ledger.compact_merkle_tree import CompactMerkleTree
from plenum.common.ledger import Ledger
from plenum.persistence.db_hash_store import DbHashStore
from storage.helper import initKeyValueStorage, initHashStore
from sovtoken.utxo_cache import UTXOCache
from state.pruning_state import PruningState


def get_token_hash_store(data_dir):
    return initHashStore(data_dir=data_dir, name='sovtoken')


def get_token_ledger(data_dir, name, hash_store, config):
    return Ledger(CompactMerkleTree(hashStore=hash_store),
                  dataDir=data_dir,
                  fileName=name,
                  ensureDurability=config.EnsureLedgerDurability)


def get_token_state(data_dir, name, config):
    return PruningState(initKeyValueStorage(
        config.tokenStateStorage, data_dir, name))


def get_utxo_cache(data_dir, name, config):
    return UTXOCache(initKeyValueStorage(
        config.utxoCacheStorage, data_dir, name))
