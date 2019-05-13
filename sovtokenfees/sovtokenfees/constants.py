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

MAX_FEE_OUTPUTS = 1