from sovtoken.constants import RESULT, OUTPUTS, SEQNO


class HelperGeneral():
    """
    Helper that uses all the other helpers.

    # Methods
    - get_utxo_addresses
    - do_mint
    - do_transfer
    - do_get_utxo
    """

    def __init__(self, helper_sdk, helper_wallet, helper_request):
        self._sdk = helper_sdk
        self._wallet = helper_wallet
        self._request = helper_request

    # =============
    # Requests
    # =============
    # Methods for creating and sending requests.

    def get_utxo_addresses(self, addresses):
        """ Get and return the utxos for each address. """
        requests = [self._request.get_utxo(address) for address in addresses]
        responses = self._sdk.send_and_check_request_objects(requests)
        utxos = [response[RESULT][OUTPUTS] for _request, response in responses]
        return utxos

    def do_mint(self, outputs):
        """ Build and send a mint request. """
        request = self._request.mint(outputs)
        return self._send_get_first_result(request)

    def do_transfer(self, inputs, outputs):
        """ Build and send a transfer request. """
        request = self._request.transfer(inputs, outputs)
        return self._send_get_first_result(request)

    def do_get_utxo(self, address):
        """ Build and send a get_utxo request. """
        request = self._request.get_utxo(address)
        result = self._send_get_first_result(request)
        result[OUTPUTS] = self._sort_utxos(result[OUTPUTS])
        return result

    # =============
    # Private Methods
    # =============

    def _send_get_first_result(self, request_object):
        responses = self._sdk.send_and_check_request_objects([request_object])
        result = self._sdk.get_first_result(responses)
        return result

    def _sort_utxos(self, utxos):
        """ Sort utxos by the seq_no. """
        utxos.sort(key=lambda utxo: utxo[SEQNO])
        return utxos
