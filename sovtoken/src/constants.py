from plenum.server.plugin.sovtoken.src.transactions import TokenTransactions

INPUTS = 'inputs'
OUTPUTS = 'outputs'
EXTRA = 'extra'
ADDRESS = 'address'
SIGS = 'signatures'

# TODO: Rename to `PAYMENT_LEDGER_ID`
TOKEN_LEDGER_ID = 1001

MINT_PUBLIC = TokenTransactions.MINT_PUBLIC.value
XFER_PUBLIC = TokenTransactions.XFER_PUBLIC.value
GET_UTXO = TokenTransactions.GET_UTXO.value
