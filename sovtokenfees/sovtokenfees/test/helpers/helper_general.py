import sovtoken.test.helpers.helper_general as token_helper_general
import base58
import json

from sovtoken.constants import ADDRESS, SEQNO


class HelperGeneral:
    """
    Extends the sovtoken HelperGeneral with fee related methods.

    # Methods
    - do_get_fees
    - do_set_fees
    """

    def do_get_fees(self):
        """ Builds and sends a get_fees request """
        request = self._request.get_fees()
        return self._send_get_first_result(request)

    def do_set_fees(self, fees):
        """ Builds and sends a set_fees request """
        request = self._request.set_fees(fees)
        return self._send_get_first_result(request)

    def set_fees_without_waiting(self, fees):
        """ Builds, sends and don't waits for a set_fees request """
        request = self._request.set_fees(fees)
        return self._send_without_waiting(request)
