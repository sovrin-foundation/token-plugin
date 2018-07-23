import json


class TxnResponse:

    version = 1

    def __init__(self, type, data, seq_no=None, signatures={}, metadata={}):
        self.type = type
        self.data = data
        self.seq_no = seq_no
        self.signatures = signatures
        self.metadata = metadata
        
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
            "reqId": self.metadata.get("reqId"),
            "from": self.metadata.get("from"),
            "digest": self.metadata.get("digest")
        }

    def _form_txn_metadata(self):
        return {
            "txnTime": None,
            "seqNo": self.seq_no,
            "txnId": None,
        }

    def _form_req_signature(self):
        values = [{"from": k, "value": v} for k, v in self.signatures.items()]
        return {
            "type": "ED25519",
            "values": values
        }

    def _form_data(self):
        data = self.data
        data.pop("type")
        return data
