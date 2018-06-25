from plenum.common.constants import TXN_SIGNATURE, TXN_SIGNATURE_TYPE, ED25519, \
    TXN_SIGNATURE_FROM, TXN_SIGNATURE_VALUE, TXN_SIGNATURE_VALUES

def add_sigs_to_txn(txn, sigs, sig_type=ED25519):
    if TXN_SIGNATURE_TYPE not in txn[TXN_SIGNATURE] or not txn[TXN_SIGNATURE][TXN_SIGNATURE_TYPE]:
        txn[TXN_SIGNATURE][TXN_SIGNATURE_TYPE] = sig_type
    if TXN_SIGNATURE_VALUES not in txn[TXN_SIGNATURE] or not txn[TXN_SIGNATURE][TXN_SIGNATURE_VALUES]:
        txn[TXN_SIGNATURE][TXN_SIGNATURE_VALUES] = []
    txn[TXN_SIGNATURE][TXN_SIGNATURE_VALUES] += [
        {
            TXN_SIGNATURE_FROM: frm,
            TXN_SIGNATURE_VALUE: sign,
        }
        for frm, sign in sigs
    ]
