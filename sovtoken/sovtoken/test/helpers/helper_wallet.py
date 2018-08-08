from sovtoken.test.wallet import Address


class HelperWallet():
    """
    Helper for dealing with the wallet and addresses.

    # Methods
    - add_new_addresses
    - payment_signatures
    - sign_request_trustees
    """

    def __init__(self, trustees):
        self._trustees = trustees

    def add_new_addresses(self, wallet, n):
        """ Create and add n new addresses to a wallet. """
        addresses = []
        for _ in range(n):
            address = Address()
            wallet.add_new_address(address=address)
            addresses.append(address)

        return addresses

    def payment_signatures(self, inputs, outputs):
        """ Generates a list of payment signatures from inptus and outputs. """
        outputs = self._prepare_outputs(outputs)
        signatures = []
        for [address, seq_no] in inputs:
            to_sign = [[[address.address, seq_no]], outputs]
            signature = address.signer.sign(to_sign)
            signatures.append(signature)
        return signatures

    def sign_request_trustees(self, request):
        """ Sign a request with trustees. """
        for trustee in self._trustees:
            trustee.do_multi_sig_on_req(request, identifier=trustee.defaultId)
        return request

    def _prepare_outputs(self, outputs):
        return [[address.address, amount] for address, amount in outputs]