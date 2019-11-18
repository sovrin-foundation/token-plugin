from sovtoken.request_handlers.batch_req_handler.token_batch_handler import TokenBatchHandler
from sovtoken.request_handlers.batch_req_handler.utxo_batch_handler import UTXOBatchHandler
from sovtoken.request_handlers.read_req_handler.get_utxo_handler import GetUtxoHandler
from sovtoken.request_handlers.write_request_handler.mint_handler import MintHandler
from sovtoken.request_handlers.write_request_handler.xfer_handler import XferHandler
from sovtoken.utxo_cache import UTXOCache

from state.pruning_state import PruningState

from storage.helper import initKeyValueStorage

from plenum.common.ledger import Ledger

from ledger.compact_merkle_tree import CompactMerkleTree
from sovtoken.sovtoken_auth_map import sovtoken_auth_map
from plenum.common.constants import DOMAIN_LEDGER_ID, KeyValueStorageType
from sovtoken.client_authnr import TokenAuthNr
from sovtoken.constants import TOKEN_LEDGER_ID, UTXO_CACHE_LABEL, ACCEPTABLE_WRITE_TYPES, ACCEPTABLE_QUERY_TYPES, \
    ACCEPTABLE_ACTION_TYPES


def integrate_plugin_in_node(node):
    update_config(node)
    node.write_req_validator.auth_map.update(sovtoken_auth_map)
    init_storages(node)
    register_req_handlers(node)
    register_batch_handlers(node)
    register_authentication(node)
    return node


def update_config(node):
    config = node.config
    config.tokenTransactionsFile = 'sovtoken_transactions'
    config.tokenStateStorage = KeyValueStorageType.Rocksdb
    config.tokenStateDbName = 'sovtoken_state'
    config.utxoCacheStorage = KeyValueStorageType.Rocksdb
    config.utxoCacheDbName = 'utxo_cache'


def init_storages(node):
    # Token ledger and state init
    if TOKEN_LEDGER_ID not in node.ledger_ids:
        node.ledger_ids.append(TOKEN_LEDGER_ID)
    token_state = init_token_state(node)
    token_ledger = init_token_ledger(node)
    node.db_manager.register_new_database(TOKEN_LEDGER_ID,
                                          token_ledger,
                                          token_state)
    init_token_database(node)

    # UTXO store init
    node.db_manager.register_new_store(UTXO_CACHE_LABEL,
                                       UTXOCache(initKeyValueStorage(
                                           node.config.utxoCacheStorage,
                                           node.dataLocation,
                                           node.config.utxoCacheDbName)))


def init_token_ledger(node):
    return Ledger(CompactMerkleTree(hashStore=node.getHashStore('sovtoken')),
                  dataDir=node.dataLocation,
                  fileName=node.config.tokenTransactionsFile,
                  ensureDurability=node.config.EnsureLedgerDurability)


def init_token_state(node):
    return PruningState(
        initKeyValueStorage(
            node.config.tokenStateStorage,
            node.dataLocation,
            node.config.tokenStateDbName,
            db_config=node.config.db_state_config)
    )


def init_token_database(node):
    node.ledgerManager.addLedger(TOKEN_LEDGER_ID,
                                 node.db_manager.get_ledger(TOKEN_LEDGER_ID),
                                 postTxnAddedToLedgerClbk=node.postTxnFromCatchupAddedToLedger)
    node.on_new_ledger_added(TOKEN_LEDGER_ID)


def register_req_handlers(node):
    node.write_manager.register_req_handler(XferHandler(node.db_manager,
                                                        node.write_req_validator))
    node.write_manager.register_req_handler(MintHandler(node.db_manager,
                                                        node.write_req_validator))
    node.read_manager.register_req_handler(GetUtxoHandler(node.db_manager, node.config.MSG_LEN_LIMIT))


def register_batch_handlers(node):
    node.write_manager.register_batch_handler(UTXOBatchHandler(node.db_manager), add_to_begin=True)
    node.write_manager.register_batch_handler(TokenBatchHandler(node.db_manager), add_to_begin=True)
    node.write_manager.register_batch_handler(node.write_manager.node_reg_handler,
                                              ledger_id=TOKEN_LEDGER_ID)
    node.write_manager.register_batch_handler(node.write_manager.audit_b_handler,
                                              ledger_id=TOKEN_LEDGER_ID)


def register_authentication(node):
    token_authnr = TokenAuthNr(ACCEPTABLE_WRITE_TYPES,
                               ACCEPTABLE_QUERY_TYPES,
                               ACCEPTABLE_ACTION_TYPES,
                               node.db_manager.idr_cache)
    node.clientAuthNr.register_authenticator(token_authnr)
