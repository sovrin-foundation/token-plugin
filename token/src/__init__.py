from plugin.token.src.constants import TOKEN_LEDGER_ID
from plugin.token.src.transactions import TokenTransactions


LEDGER_IDS = {TOKEN_LEDGER_ID, }
AcceptableWriteTypes = {TokenTransactions.MINT_PUBLIC.value,
                        TokenTransactions.XFER_PUBLIC.value}

AcceptableQueryTypes = {TokenTransactions.GET_UTXO.value, }
