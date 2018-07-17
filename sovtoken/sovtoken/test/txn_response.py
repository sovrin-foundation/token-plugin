import json


class TxnResponse:

    version = 1

    def __init__(self, type, data, seq_no=None):
        self.type = type
        self.data = data
        self.seq_no = seq_no
        

    def form_response(self):
        txn_metadata = self._form_txn_metadata()
        metadata = self._form_metadata()
        req_signature = self._form_req_signature()
        data = self._form_data()

        response = {
            "ver": self.version,
            "protocolVersion": 2,
            "txn": {
                "type": self.type,
                "metadata": metadata,
                "data": data,
            },
            "txnMetadata": txn_metadata,
            "reqSignature": req_signature,
        }

        return response

    def form_response_json(self):
        response = self.form_response()
        return json.dumps(response)

    def _form_metadata(self):
        return {
            "reqId": None,
            "from": None,
        }

    def _form_txn_metadata(self):
        return {
            'txnTime': None,
            'seqNo': self.seq_no,
            'txnId': None,
        }

    def _form_req_signature(self):
        return {
            "type": None,
            "values": None
        }

    def _form_data(self):
        if not "ver" in self.data:
            self.data["ver"] = self.version
        return self.data