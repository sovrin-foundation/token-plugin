import json

from plenum.common.constants import TXN_TYPE, TXN_PAYLOAD, TXN_PAYLOAD_METADATA, \
    TXN_PAYLOAD_DATA, TXN_PAYLOAD_METADATA_FROM, TXN_PAYLOAD_METADATA_REQ_ID, \
    TXN_PAYLOAD_METADATA_DIGEST, TXN_METADATA, TXN_SIGNATURE, TXN_VERSION, \
    TXN_PAYLOAD_PROTOCOL_VERSION, TXN_SIGNATURE_FROM, TXN_SIGNATURE_VALUE, \
    TXN_SIGNATURE_VALUES, TXN_SIGNATURE_TYPE, ED25519, TXN_METADATA_TIME, \
    TXN_METADATA_ID, TXN_METADATA_SEQ_NO, CURRENT_TXN_VERSIONS


def get_sorted_signatures(txn_response):
    signatures = txn_response[TXN_SIGNATURE]
    signatures[TXN_SIGNATURE_VALUES].sort(key=lambda fv: fv[TXN_SIGNATURE_FROM])
    return signatures


class TxnResponse:

    def __init__(self,
                 type,
                 data,
                 seq_no=None,
                 signatures={},
                 frm=None,
                 req_id=None,
                 digest=None):

        self.type = type
        self.data = data
        self.seq_no = seq_no
        self.signatures = signatures
        self.frm = frm
        self.req_id = req_id
        self.digest = digest

    def form_response(self):
        txn_metadata = self._form_txn_metadata()
        metadata = self._form_metadata()
        req_signature = self._form_req_signature()
        data = self._form_data()

        response = {
            TXN_VERSION: CURRENT_TXN_VERSIONS[self.type],
            TXN_PAYLOAD_PROTOCOL_VERSION: 2,
            TXN_PAYLOAD: {
                TXN_TYPE: self.type,
                TXN_PAYLOAD_METADATA: metadata,
                TXN_PAYLOAD_DATA: data,
            },
            TXN_METADATA: txn_metadata,
            TXN_SIGNATURE: req_signature,
        }

        return response

    def form_response_json(self):
        response = self.form_response()
        return json.dumps(response)

    def _form_metadata(self):
        return {
            TXN_PAYLOAD_METADATA_REQ_ID: self.req_id,
            TXN_PAYLOAD_METADATA_FROM: self.frm,
            TXN_PAYLOAD_METADATA_DIGEST: self.digest,
        }

    def _form_txn_metadata(self):
        return {
            TXN_METADATA_TIME: None,
            TXN_METADATA_SEQ_NO: self.seq_no,
            TXN_METADATA_ID: None,
        }

    def _form_req_signature(self):
        values = [
            {TXN_SIGNATURE_FROM: k, TXN_SIGNATURE_VALUE: v}
            for k, v in self.signatures.items()
        ]
        return {
            TXN_SIGNATURE_TYPE: ED25519,
            TXN_SIGNATURE_VALUES: values
        }

    def _form_data(self):
        data = self.data
        data.pop(TXN_TYPE)
        return data

