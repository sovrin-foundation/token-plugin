import json

from indy import did
from indy.payment import create_payment_address
from plenum.common.util import randomString
from plenum.common.txn_util import get_payload_data, get_seq_no

from sovtoken.constants import INPUTS, OUTPUTS


class HelperWallet():
    """
    Helper for dealing with the wallet and addresses.

    # Methods
    - add_new_addresses
    - create_address
    - create_client_wallet
    - create_new_addresses
    - sign_request
    - sign_request_trustees
    - sign_request_stewards
    """

    def __init__(self, looper, client_wallet, trustee_wallets, steward_wallets):
        self._looper = looper
        self._client_wallet = client_wallet
        self._trustee_wallets = trustee_wallets
        self._steward_wallets = steward_wallets
        self.address_map = {}

    def create_address(self):
        """ Create a new address and add it to the address_map """
        address = create_payment_address(self._client_wallet[0], "sov", "{}")
        address = self._looper.loop.run_until_complete(address)
        return address

    def create_new_addresses(self, n):
        """ Create n new addresses """
        return [self.create_address() for _ in range(n)]

    def create_did(self, seed=None, sdk_wallet=None):
        """ Create and store a did in a sdk_wallet. """
        if not seed:
            seed = randomString(32)

        sdk_wallet = sdk_wallet or self._client_wallet

        wallet_handle, _ = sdk_wallet
        config = json.dumps({seed: seed})
        future = did.create_and_store_my_did(wallet_handle, config)

        return self._looper.loop.run_until_complete(future)

    def sign_request_trustees(self, request, number_signers=4):
        """ Sign a request with trustees. """
        assert number_signers <= len(self._trustee_wallets)
        return self.sign_request(request, self._trustee_wallets[:number_signers])

    def sign_request_stewards(self, request, number_signers=4):
        """ Sign a request with stewards. """
        assert number_signers <= len(self._steward_wallets)
        return self.sign_request(request, self._steward_wallets[:number_signers])

    def sign_request(self, request, wallets):
        """ Sign a request with wallets from plenum/client/wallet """
        for wallet in wallets:
            wallet.do_multi_sig_on_req(request, identifier=wallet.defaultId)
        return request

    def _prepare_outputs(self, outputs):
        return [{"address": address, "amount": amount} for address, amount in outputs]

    def handle_get_utxo_response(self, response):
        self._update_outputs(response[OUTPUTS])

    def handle_xfer(self, response):
        data = get_payload_data(response)
        seq_no = get_seq_no(response)
        self._update_inputs(data[INPUTS])
        self._update_outputs(data[OUTPUTS], seq_no)

    def _update_inputs(self, inputs):
        for inp in inputs:
            addr = inp["address"]
            seq_no = inp["seqNo"]
            if addr in self.address_map:
                self.address_map[addr].spent(seq_no)

    def _update_outputs(self, outputs, txn_seq_no=None):
        for output in outputs:
            try:
                addr = output["address"]
                val = output["amount"]
                try:
                    seq_no = output["seqNo"]
                except KeyError as ex:
                    if txn_seq_no and isinstance(txn_seq_no, int):
                        seq_no = txn_seq_no
                    else:
                        raise ex
            except Exception:
                raise ValueError('Cannot handle output {}'.format(output))
            if addr in self.address_map:
                self.address_map[addr].add_utxo(seq_no, val)