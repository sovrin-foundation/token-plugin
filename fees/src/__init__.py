from plenum.server.plugin.fees.src.messages.fields import TxnFeesField
from plenum.server.plugin.fees.src.transactions import FeesTransactions

# TODO: Fix this, use a constant
CLIENT_REQUEST_FIELDS = {
    'fees': TxnFeesField(optional=True, nullable=True),
}

AcceptableWriteTypes = {FeesTransactions.SET_FEES.value, }

AcceptableQueryTypes = {FeesTransactions.GET_FEES.value, }
