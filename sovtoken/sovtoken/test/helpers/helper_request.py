from plenum.common.constants import TXN_TYPE, CURRENT_PROTOCOL_VERSION
from plenum.common.request import Request
from sovtoken.constants import INPUTS, OUTPUTS, EXTRA, SIGS, XFER_PUBLIC, \
    MINT_PUBLIC
from sovtoken.util import address_to_verkey


class HelperRequest():
    """
    Helper to build different requests.

    # methods
    - transfer
    - mint
    """

    def __init__(self, helper_wallet):
        self.wallet = helper_wallet

    def transfer(self, inputs, outputs, extra=None):
        """ Builds a transfer request """
        outputs_ready = self._prepare_outputs(outputs)
        inputs_ready = [[address.address, seq_no] for address, seq_no in inputs]

        [first_address, seq_no] = inputs_ready[0]
        payment_signatures = self.wallet.payment_signatures(inputs, outputs_ready)

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
        outputs_ready = self._prepare_outputs(outputs)

        payload = {
            TXN_TYPE: MINT_PUBLIC,
            OUTPUTS: outputs_ready,
        }

        request = self._create_request(payload)
        request = self.wallet.sign_request_trustees(request)
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
