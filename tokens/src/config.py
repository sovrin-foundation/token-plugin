from plenum.common.constants import KeyValueStorageType


def get_config(config):
    config.tokenTransactionsFile = 'token_transactions'
    config.tokenStateStorage = KeyValueStorageType.Leveldb
    config.tokenStateDbName = 'token_state'
    config.utxoCacheStorage = KeyValueStorageType.Leveldb
    config.utxoCacheDbName = 'utxo_cache'
    return config
