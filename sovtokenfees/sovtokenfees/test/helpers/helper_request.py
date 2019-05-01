import json

from indy.payment import add_request_fees, build_set_txn_fees_req, build_get_txn_fees_req
from sovtoken.test.helpers import HelperRequest
from sovtokenfees.constants import FEES
from sovtokenfees.test.helpers.abstract_helper_request import AbstractHelperRequest

from stp_core.common.log import getlogger

logger = getlogger()


class HelperRequest(AbstractHelperRequest, HelperRequest):
    """
    Extends the sovtoken HelperRequest with fee related requests.

    # Methods
    - set_fees
    - get_fees
    - add_fees
    - add_fees_specific
    - find_utxos_can_pay
    - fees_signatures
    """

    def set_fees(self, fees):
        """ Build a request to set the fees. """

        request = build_set_txn_fees_req(self._client_wallet_handle, None, 'sov', json.dumps(fees))
        request = self._looper.loop.run_until_complete(request)
        request = self._sdk.sdk_json_to_request_object(json.loads(request))
        request = self._wallet.sign_request_trustees(request, number_signers=3)
        return request

    def get_fees(self):
        """ Build a request to get the fees. """
        request = build_get_txn_fees_req(self._client_wallet_handle, None, 'sov')
        request = self._looper.loop.run_until_complete(request)
        request = self._sdk.sdk_json_to_request_object(json.loads(request))
        return request

    def add_fees_to_req(self, request, inputs, outputs):
        request_with_fees_future = add_request_fees(self._client_wallet_handle, None, json.dumps(request.as_dict),
                                                    json.dumps(inputs), json.dumps(outputs), None)
        return self._looper.loop.run_until_complete(request_with_fees_future)

