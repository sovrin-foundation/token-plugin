import functools
from sovtoken.sovtoken_auth_map import sovtoken_auth_map
from plenum.common.constants import DOMAIN_LEDGER_ID, NodeHooks
from sovtoken.client_authnr import TokenAuthNr
from sovtoken.config import get_config
from sovtoken.constants import TOKEN_LEDGER_ID
from sovtoken.storage import get_token_hash_store, \
    get_token_ledger, get_token_state, get_utxo_cache
from sovtoken.token_req_handler import TokenReqHandler


def integrate_plugin_in_node(node):

    node.config = get_config(node.config)
    node.write_req_validator.auth_map.update(sovtoken_auth_map)

    token_authnr = TokenAuthNr(node.states[DOMAIN_LEDGER_ID])
    hash_store = get_token_hash_store(node.dataLocation)
    ledger = get_token_ledger(node.dataLocation,
                              node.config.tokenTransactionsFile,
                              hash_store, node.config)
    state = get_token_state(node.dataLocation,
                            node.config.tokenStateDbName,
                            node.config)
    utxo_cache = get_utxo_cache(node.dataLocation,
                                node.config.utxoCacheDbName,
                                node.config)

    if TOKEN_LEDGER_ID not in node.ledger_ids:
        node.ledger_ids.append(TOKEN_LEDGER_ID)

    node.ledgerManager.addLedger(TOKEN_LEDGER_ID, ledger,
                                 postTxnAddedToLedgerClbk=node.postTxnFromCatchupAddedToLedger)
    node.on_new_ledger_added(TOKEN_LEDGER_ID)
    node.register_state(TOKEN_LEDGER_ID, state)
    node.clientAuthNr.register_authenticator(token_authnr)

    token_req_handler = TokenReqHandler(ledger, state, utxo_cache,
                                        node.states[DOMAIN_LEDGER_ID], node.bls_bft.bls_store,
                                        node.write_req_validator)
    node.register_req_handler(token_req_handler, TOKEN_LEDGER_ID)
    node.db_manager.register_new_database(lid=TOKEN_LEDGER_ID,
                                          ledger=ledger,
                                          state=state)
    return node
