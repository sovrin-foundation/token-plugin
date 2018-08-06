from sovtoken.constants import RESULT, OUTPUTS


class HelperGeneral():
    """
    Helper that uses all the other helpers.

    # Methods
    - get_utxo_addresses
    """

    def __init__(self, helper_sdk, helper_wallet, helper_request):
        self._sdk = helper_sdk
        self._wallet = helper_wallet
        self._request = helper_request

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

    def _get_utxo_addresses(self, addresses):
        requests = [self._request.get_utxo(address) for address in addresses]
        responses = self._sdk.send_and_check_request_objects(requests)
        utxos = [response[RESULT][OUTPUTS] for _request, response in responses]
        return utxos
