from sovtokenfees.transactions import FeesTransactions

FEES = 'fees'
FEE = 'fee'
REF = 'ref'
FEE_TXNS_IN_BATCH = 'fee_txns_in_batch'
# Its "seqNo" and not "seq_no" to be consistent with the current replies
FEES_SEQ_NO = 'fees_seqNo'

SET_FEES = FeesTransactions.SET_FEES.value
GET_FEES = FeesTransactions.GET_FEES.value
GET_FEE = FeesTransactions.GET_FEE.value
FEE_TXN = FeesTransactions.FEES.value

FEES_STATE_PREFIX = '200'
FEES_KEY_DELIMITER = ':'
FEES_KEY_FOR_ALL = 'fees'
FEES_FIELD_NAME = 'fees'
FEE_ALIAS_LENGTH = 128

MAX_FEE_OUTPUTS = 1

ACCEPTABLE_WRITE_TYPES_FEE = {FeesTransactions.SET_FEES.value, }
ACCEPTABLE_QUERY_TYPES_FEE = {FeesTransactions.GET_FEES.value,
                              FeesTransactions.GET_FEE.value}
ACCEPTABLE_ACTION_TYPES_FEE = {}
