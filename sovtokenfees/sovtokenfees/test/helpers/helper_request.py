import json

from indy.payment import add_request_fees
from sovtoken.test.helpers import HelperRequest
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

    def add_fees_to_req(self, request, inputs, outputs):
        request_with_fees_future = add_request_fees(self._client_wallet_handle, None, json.dumps(request.as_dict),
                                                    json.dumps(inputs), json.dumps(outputs), None)
        return self._looper.loop.run_until_complete(request_with_fees_future)

    def inject_fees_specific(self, request, inputs, outputs):
        """
        Sign the fees and add them to a request.
        """
        fees_signatures = self.fees_signatures(inputs, outputs, request.payload_digest)

        fees = [inputs, outputs, fees_signatures]
        setattr(request, FEES, fees)

        return request

