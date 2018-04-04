from plenum.server.plugin.token.src.transactions import TokenTransactions

INPUTS = 'inputs'
OUTPUTS = 'outputs'
EXTRA = 'extra'
ADDRESS = 'address'

TOKEN_LEDGER_ID = 1001

MINT_PUBLIC = TokenTransactions.MINT_PUBLIC.value
XFER_PUBLIC = TokenTransactions.XFER_PUBLIC.value
GET_UTXO = TokenTransactions.GET_UTXO.value
