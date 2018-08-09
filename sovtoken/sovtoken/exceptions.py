from plenum.common.exceptions import InvalidClientMessageException


class InsufficientFundsError(InvalidClientMessageException):
    pass


class ExtraFundsError(InvalidClientMessageException):
    pass


class UTXOAlreadySpentError(InvalidClientMessageException):
    pass
