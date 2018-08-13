from enum import Enum, unique

# DO NOT CHANGE ONCE CODE IS DEPLOYED ON THE LEDGER
PREFIX = '2000'


@unique
class FeesTransactions(Enum):
    #  These numeric constants CANNOT be changed once they have been used,
    #  because that would break backwards compatibility with the ledger
    # Also the numeric constants CANNOT collide with other transactions hence a
    # prefix is used
    SET_FEES = PREFIX + '0'
    GET_FEES = PREFIX + '1'
    FEES = PREFIX + '2'

    def __str__(self):
        return self.name
