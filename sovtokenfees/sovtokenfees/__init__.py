from sovtokenfees.__metadata__ import *

from sovtokenfees.messages.fields import TxnFeesField
from sovtokenfees.transactions import FeesTransactions

# TODO: Fix this, use a constant
CLIENT_REQUEST_FIELDS = {
    'fees': TxnFeesField(optional=True, nullable=True),
}

AcceptableWriteTypes = {FeesTransactions.SET_FEES.value, }

AcceptableQueryTypes = {FeesTransactions.GET_FEES.value, }
