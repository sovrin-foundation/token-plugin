from sovtoken.test.wallet import Address


class HelperWallet():
    """
    Helper for dealing with the wallet and addresses.

    # Methods
    - add_new_addresses
    - payment_signatures
    - sign_request_trustees
    - sign_request_stewards
    """

    def __init__(self, trustee_wallets, steward_wallets):
        self._trustee_wallets = trustee_wallets
        self._steward_wallets = steward_wallets

    def create_address(self):
        return Address()

    def add_new_addresses(self, wallet, n):
        """ Create and add n new addresses to a wallet. """
        addresses = []
        for _ in range(n):
            address = Address()
            wallet.add_new_address(address=address)
            addresses.append(address)

        return addresses

    def payment_signatures(self, inputs, outputs):
        """ Generate a list of payment signatures from inptus and outputs. """
        outputs = self._prepare_outputs(outputs)
        signatures = []
        for [address, seq_no] in inputs:
            to_sign = [[[address.address, seq_no]], outputs]
            signature = address.signer.sign(to_sign)
            signatures.append(signature)
        return signatures

    def sign_request_trustees(self, request):
        """ Sign a request with trustees. """
        return self._sign_request(request, self._trustee_wallets)

    def sign_request_stewards(self, request):
        """ Sign a request with stewards. """
        return self._sign_request(request, self._steward_wallets)

    def _sign_request(self, request, wallets):
        for wallet in wallets:
            wallet.do_multi_sig_on_req(request, identifier=wallet.defaultId)
        return request

    def _prepare_outputs(self, outputs):
        return [[address.address, amount] for address, amount in outputs]
