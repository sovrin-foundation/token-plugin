from plenum.common.exceptions import InvalidClientMessageException
from common.exceptions import PlenumValueError


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


class UTXONotFound(UTXOError):  # noqa: N818
    pass


class UTXOAddressNotFound(UTXONotFound):  # noqa: N818
    pass


class UTXOAlreadySpentError(UTXOError):
    pass


class TokenValueError(PlenumValueError):
    pass
