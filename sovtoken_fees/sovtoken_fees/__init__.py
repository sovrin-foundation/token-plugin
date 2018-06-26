from sovtoken_fees.__metadata__ import *

from sovtoken_fees.messages.fields import TxnFeesField
from sovtoken_fees.transactions import FeesTransactions

# TODO: Fix this, use a constant
CLIENT_REQUEST_FIELDS = {
    'fees': TxnFeesField(optional=True, nullable=True),
}

AcceptableWriteTypes = {FeesTransactions.SET_FEES.value, }

AcceptableQueryTypes = {FeesTransactions.GET_FEES.value, }
