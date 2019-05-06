import json

from indy.ledger import build_nym_request, build_schema_request
from plenum.common.constants import TXN_TYPE, CURRENT_PROTOCOL_VERSION, GET_TXN, DATA
from plenum.common.request import Request
from plenum.common.types import f
from sovtoken.constants import INPUTS, OUTPUTS, EXTRA, SIGS, XFER_PUBLIC, \
    MINT_PUBLIC, GET_UTXO, ADDRESS, SEQNO, AMOUNT
from sovtoken.util import address_to_verkey


class HelperRequest():
    """
    Helper to build different requests.

    # methods
    - get_utxo
    - transfer
    - mint
    - nym
    - payment_signatures
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
            ADDRESS: address
        }

        request = self._create_request(payload, self._client_did)

        return request

    def get_txn(self, ledger_id, seq_no):
        """ Builds a get_txn request. """
        payload = {
            TXN_TYPE: GET_TXN,
            f.LEDGER_ID.nm: ledger_id,
            DATA: seq_no
        }
        request = self._create_request(payload, self._client_did)

        return request

    def transfer(self, inputs, outputs, extra=None, identifier=None):
        """ Builds a transfer request. """
        payment_signatures = self.payment_signatures(inputs, outputs)

        outputs_ready = self._prepare_outputs(outputs)
        inputs_ready = self._prepare_inputs(inputs)

        payload = {
            TXN_TYPE: XFER_PUBLIC,
            OUTPUTS: outputs_ready,
            INPUTS: inputs_ready,
            EXTRA: extra,
            SIGS: payment_signatures
        }

        if not identifier:
            first_address = inputs_ready[0][ADDRESS]
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

        request = self._create_request(payload,
                                       identifier=self._wallet._trustee_wallets[0].defaultId)
        request = self._wallet.sign_request_trustees(request, number_signers=3)
        return request

    def nym(
        self,
        seed=None,
        alias=None,
        role=None,
        dest=None,
        verkey=None,
        sdk_wallet=None,
    ):
        """
        Builds a nym request.

        Role can be:
            None  => No change,
            ''    => Standard User,
            '0'   => Trustee,
            '2'   => Steward,
            '101' => Trust Anchor,
        """
        sdk_wallet_did = self._find_wallet_did(sdk_wallet)

        if not dest:
            (dest, new_verkey) = self._wallet.create_did(
                seed=seed,
                sdk_wallet=sdk_wallet
            )
            verkey = new_verkey

        nym_request_future = build_nym_request(
            sdk_wallet_did,
            dest,
            verkey,
            alias,
            role,
        )

        nym_request = self._looper.loop.run_until_complete(nym_request_future)
        request = self._sdk.sdk_json_to_request_object(json.loads(nym_request))
        request = self._sign_sdk(request, sdk_wallet=sdk_wallet)

        return request

    def schema(
            self,
            schema_data,
            sdk_wallet=None
    ):
        sdk_wallet_did = self._find_wallet_did(sdk_wallet)
        schema_request_future = build_schema_request(sdk_wallet_did, schema_data)
        schema_request = self._looper.loop.run_until_complete(schema_request_future)
        request = self._sdk.sdk_json_to_request_object(json.loads(schema_request))
        request = self._sign_sdk(request, sdk_wallet=sdk_wallet)
        return request

    def _find_wallet_did(self, sdk_wallet):
        sdk_wallet = sdk_wallet or self._steward_wallet
        _, sdk_wallet_did = sdk_wallet
        return sdk_wallet_did

    def payment_signatures(self, inputs, outputs):
        """ Generate a list of payment signatures from inptus and outputs. """
        signatures = []
        inputs = self._prepare_inputs(inputs)
        outputs = self._prepare_outputs(outputs)

        for utxo in inputs:
            to_sign = [[utxo], outputs]
            signer = self._wallet.get_address_instance(utxo[ADDRESS]).signer
            signature = signer.sign(to_sign)
            signatures.append(signature)

        return signatures

    def _prepare_outputs(self, outputs):
        return [
            {ADDRESS: output[ADDRESS], AMOUNT: output[AMOUNT]}
            for output in outputs
        ]

    def _prepare_inputs(self, inputs):
        return [
            {ADDRESS: utxo[ADDRESS], SEQNO: utxo[SEQNO]}
            for utxo in inputs
        ]

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
