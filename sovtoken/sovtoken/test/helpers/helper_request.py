import json

from plenum.common.constants import TXN_TYPE, CURRENT_PROTOCOL_VERSION
from plenum.common.request import Request
from plenum.common.util import randomString
from sovtoken.constants import INPUTS, OUTPUTS, EXTRA, SIGS, XFER_PUBLIC, \
    MINT_PUBLIC, GET_UTXO, ADDRESS
from sovtoken.util import address_to_verkey
from plenum.test.pool_transactions.helper import prepare_nym_request


class HelperRequest():
    """
    Helper to build different requests.

    # methods
    - get_utxo
    - transfer
    - mint
    """

    def __init__(
        self,
        helper_wallet,
        helper_sdk,
        looper,
        client_wallet,
        steward_wallet
    ):
        self._wallet = helper_wallet
        self._sdk = helper_sdk
        self._looper = looper
        self._client_wallet_handle = client_wallet[0]
        self._client_did = client_wallet[1]
        self._client_wallet = client_wallet
        self._steward_wallet = steward_wallet

    def get_utxo(self, address):
        """ Builds a get_utxo request. """
        payload = {
            TXN_TYPE: GET_UTXO,
            ADDRESS: address.address
        }

        request = self._create_request(payload, self._client_did)

        return request

    def transfer(self, inputs, outputs, extra=None):
        """ Builds a transfer request. """
        outputs_ready = self._prepare_outputs(outputs)
        inputs_ready = [[address.address, seq_no] for address, seq_no in inputs]

        [first_address, seq_no] = inputs_ready[0]
        payment_signatures = self._wallet.payment_signatures(inputs, outputs)

        payload = {
            TXN_TYPE: XFER_PUBLIC,
            OUTPUTS: outputs_ready,
            INPUTS: inputs_ready,
            EXTRA: extra,
            SIGS: payment_signatures
        }

        identifier = address_to_verkey(first_address)
        request = self._create_request(payload, identifier)

        return request

    def mint(self, outputs):
        """ Builds a mint request. """
        outputs_ready = self._prepare_outputs(outputs)

        payload = {
            TXN_TYPE: MINT_PUBLIC,
            OUTPUTS: outputs_ready,
        }

        request = self._create_request(payload)
        request = self._wallet.sign_request_trustees(request)
        return request

    def nym(
        self,
        seed=None,
        alias=None,
        role=None,
        sdk_wallet=None
    ):
        """ Builds a nym request. """
        if not seed:
            seed = randomString(32)
  
        if not alias:
            alias = randomString(6)

        sdk_wallet = sdk_wallet or self._steward_wallet

        nym_request_future = prepare_nym_request(
            sdk_wallet,
            seed,
            alias,
            role
        )

        nym_request, _did = self._looper.loop.run_until_complete(nym_request_future)
        request = self._sdk.sdk_json_to_request_object(json.loads(nym_request))
        request = self._sign_sdk(request, sdk_wallet=sdk_wallet)

        return request

    def _prepare_outputs(self, outputs):
        return [[address.address, amount] for address, amount in outputs]

    def _create_request(self, payload, identifier=None):
        return Request(
            reqId=Request.gen_req_id(),
            operation=payload,
            protocolVersion=CURRENT_PROTOCOL_VERSION,
            identifier=identifier
        )

    # Copied this over from another helper. Don't really know what it does.
    def _sign_sdk(self, request, sdk_wallet=None):
        request = self._sdk.sdk_sign_request_objects(
            [request],
            sdk_wallet=sdk_wallet
        )[0]

        request = self._sdk.sdk_json_to_request_object(json.loads(request))

        if request.signatures is None:
            request.signatures = {}

        request.signatures[request._identifier] = request.signature
        request.signature = None
        request._identifier = None

        return request
