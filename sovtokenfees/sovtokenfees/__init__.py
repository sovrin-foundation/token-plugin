import sovtokenfees.__metadata__

from sovtokenfees.transactions import FeesTransactions
from sovtokenfees.messages.fields import TxnFeesField

# TODO: Fix this, use a constant
CLIENT_REQUEST_FIELDS = {
    'fees': TxnFeesField(optional=True, nullable=True),
}

# TODO: Find a better way to import all members of this module
__all__ = [
    CLIENT_REQUEST_FIELDS,
]
