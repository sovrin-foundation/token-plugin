from enum import Enum, unique

from plenum.common.transactions import Transactions


# DO NOT CHANGE ONCE CODE IS DEPLOYED ON THE LEDGER
PREFIX = '1000'


class TokenTransactions(Transactions):
    #  These numeric constants CANNOT be changed once they have been used,
    #  because that would break backwards compatibility with the ledger
    # Also the numeric constants CANNOT collide with other transactions hence a
    # prefix is used
    MINT_PUBLIC = PREFIX + '0'
    XFER_PUBLIC = PREFIX + '1'
    GET_UTXO = PREFIX + '2'
