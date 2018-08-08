from plenum.common.exceptions import InvalidClientMessageException


class InsufficientFundsError(InvalidClientMessageException):
    pass


class InvalidFundsError(InvalidClientMessageException):
    pass


class UTXOError(Exception):
    pass


class UTXONotFound(UTXOError):
    pass


class UTXOAlreadySpentError(UTXOError):
    pass
