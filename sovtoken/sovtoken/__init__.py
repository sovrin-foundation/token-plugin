from sovtoken.__metadata__ import *

from sovtoken.constants import TOKEN_LEDGER_ID
from sovtoken.transactions import TokenTransactions

LEDGER_IDS = {TOKEN_LEDGER_ID, }
AcceptableWriteTypes = {TokenTransactions.MINT_PUBLIC.value,
                        TokenTransactions.XFER_PUBLIC.value}

AcceptableQueryTypes = {TokenTransactions.GET_UTXO.value, }
