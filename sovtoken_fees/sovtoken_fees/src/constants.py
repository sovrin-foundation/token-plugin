from sovtoken_fees.src.transactions import FeesTransactions

FEES = 'fees'
REF = 'ref'
FEE_TXNS_IN_BATCH = 'fee_txns_in_batch'
# Its "seqNo" and not "seq_no" to be consistent with the current replies
FEES_SEQ_NO = 'fees_seqNo'

SET_FEES = FeesTransactions.SET_FEES.value
GET_FEES = FeesTransactions.GET_FEES.value
