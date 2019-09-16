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

    def do_get_fee(self, alias):
        """ Builds and sends a get_fees request """
        request = self._request.get_fee(alias)
        return self._send_get_first_result(request)

    def do_set_fees(self, fees, fill_auth_map=True):
        """ Builds and sends a set_fees request """
        request = self._request.set_fees(fees)
        res = self._send_get_first_result(request)
        if fill_auth_map:
            self._node.set_fees_directly(fees)
        return res

    def set_fees_without_waiting(self, fees, fill_auth_map=True):
        """ Builds, sends and don't waits for a set_fees request """
        request = self._request.set_fees(fees)
        res = self._send_without_waiting(request)
        if fill_auth_map:
            self._node.set_fees_directly(fees)
        return res

    def get_txn(self, ledger_id, seq_no):
        request = self._request.get_txn(ledger_id, seq_no)
        res = self._send_get_first_result(request, sign=False)
        return res
