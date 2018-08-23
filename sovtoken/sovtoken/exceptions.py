from plenum.common.exceptions import InvalidClientMessageException


class InsufficientFundsError(InvalidClientMessageException):
    pass


class InvalidFundsError(InvalidClientMessageException):
    pass


class ExtraFundsError(InvalidClientMessageException):
    pass


# class AddressNotFound(Exception):
#     pass


class UTXOError(Exception):
    pass


class UTXONotFound(UTXOError):
    pass


class UTXOAddressNotFound(UTXONotFound):
    pass

class UTXOAlreadySpentError(UTXOError):
    pass
