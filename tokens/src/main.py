from plenum.common.constants import DOMAIN_LEDGER_ID
from tokens.src.client_authnr import TokenAuthNr
from tokens.src.config import get_config
from tokens.src.constants import TOKEN_LEDGER_ID
from tokens.src.storage import get_token_hash_store, \
    get_token_ledger, get_token_state, get_utxo_cache
from tokens.src.token_req_handler import TokenReqHandler


def update_node_obj(node):
    node.config = get_config(node.config)

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
                                        node.states[DOMAIN_LEDGER_ID])
    node.register_req_handler(TOKEN_LEDGER_ID, token_req_handler)

    return node
