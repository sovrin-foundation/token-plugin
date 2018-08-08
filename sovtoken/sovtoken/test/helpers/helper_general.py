from sovtoken.constants import RESULT, OUTPUTS


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
        def replace_utxos_address(utxos, address):
            for utxo in utxos:
                utxo[0] = address
            return utxos

        utxos = self._get_utxo_addresses(addresses)

        utxos_with_address_object = []
        for address_utxos, address in zip(utxos, addresses):
            # Sort by sequence number
            address_utxos.sort(key=lambda utxos: utxos[1])
            # replace address string with Address object
            address_utxos = replace_utxos_address(address_utxos, address)
            utxos_with_address_object.append(address_utxos)

        return utxos_with_address_object

    def do_mint(self, outputs):
        """ Builds and sends a mint request """
        request = self._request.mint(outputs)
        return self._send_get_first_result(request)

    def do_transfer(self, inputs, outputs):
        """ Builds and sends a transfer request """
        request = self._request.transfer(inputs, outputs)
        return self._send_get_first_result(request)

    def do_get_utxo(self, address):
        """ Builds and sends a get_utxo request """
        request = self._request.get_utxo(address)
        return self._send_get_first_result(request)

    # =============
    # Private Methods
    # =============

    def _get_utxo_addresses(self, addresses):
        requests = [self._request.get_utxo(address) for address in addresses]
        responses = self._sdk.send_and_check_request_objects(requests)
        utxos = [response[RESULT][OUTPUTS] for _request, response in responses]
        return utxos

    def _send_get_first_result(self, request_object):
        responses = self._sdk.send_and_check_request_objects([request_object])
        result = self._sdk.get_first_result(responses)
        return result
