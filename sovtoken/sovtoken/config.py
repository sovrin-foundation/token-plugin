from plenum.common.constants import KeyValueStorageType


def get_config(config):
    config.tokenTransactionsFile = 'sovtoken_transactions'
    config.tokenStateStorage = KeyValueStorageType.Rocksdb
    config.tokenStateDbName = 'sovtoken_state'
    config.utxoCacheStorage = KeyValueStorageType.Rocksdb
    config.utxoCacheDbName = 'utxo_cache'
    return config
