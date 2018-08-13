from plenum.common.exceptions import InvalidClientMessageException


class InsufficientFundsError(InvalidClientMessageException):
    pass


class InvalidFundsError(InvalidClientMessageException):
    pass


class ExtraFundsError(InvalidClientMessageException):
    pass
