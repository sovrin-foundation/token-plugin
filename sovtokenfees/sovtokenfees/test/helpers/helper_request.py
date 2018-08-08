import sovtoken.test.helpers.helper_request as token_helper_request

from plenum.common.constants import TXN_TYPE
from sovtokenfees.constants import SET_FEES, FEES, GET_FEES


class HelperRequest(token_helper_request.HelperRequest):
    """
    Extends the sovtoken HelperRequest with fee related requests.

    # Methods
    - set_fees
    - get_fees
    """

    def set_fees(self, fees):
        """ Builds a request to set the fees """
        payload = {
            TXN_TYPE: SET_FEES,
            FEES: fees,
        }

        request = self._create_request(payload)
        request = self._wallet.sign_request_trustees(request)
        return request

    def get_fees(self):
        """ Builds a request to get the fees """
        payload = {
            TXN_TYPE: GET_FEES
        }

        request = self._create_request(payload)
        return request
