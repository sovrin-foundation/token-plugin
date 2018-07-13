from plenum.common.exceptions import InvalidClientMessageException

class InsufficientFundsError(InvalidClientMessageException):
    pass

class UTXOAlreadySpentError(InvalidClientMessageException):
    pass