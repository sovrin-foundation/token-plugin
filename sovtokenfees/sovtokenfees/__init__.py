from sovtokenfees.__metadata__ import *

from sovtokenfees.transactions import FeesTransactions
from sovtokenfees.messages.fields import TxnFeesField

# TODO: Fix this, use a constant
CLIENT_REQUEST_FIELDS = {
    'fees': TxnFeesField(optional=True, nullable=True),
}

AcceptableWriteTypes = {FeesTransactions.SET_FEES.value, }

AcceptableQueryTypes = {FeesTransactions.GET_FEES.value, FeesTransactions.GET_FEE.value}


# TODO: Find a better way to import all members of this module
__all__ = [
    CLIENT_REQUEST_FIELDS,
    AcceptableQueryTypes,
    AcceptableWriteTypes
]
