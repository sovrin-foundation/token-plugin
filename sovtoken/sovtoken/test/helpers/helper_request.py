from plenum.common.constants import TXN_TYPE, CURRENT_PROTOCOL_VERSION
from plenum.common.request import Request
from sovtoken.constants import INPUTS, OUTPUTS, EXTRA, SIGS, XFER_PUBLIC
from sovtoken.util import address_to_verkey


class HelperRequest():
    """
    Helper to build different requests.

    # methods
    - transfer
    """

    def transfer(self, inputs, outputs, extra=None):
        """ Builds a transfer request """
        outputs_ready = [[address.address, amount] for address, amount in outputs]
        inputs_ready = [[address.address, seq_no] for address, seq_no in inputs]

        [first_address, seq_no] = inputs_ready[0]
        payment_signatures = self._payment_signatures(inputs, outputs_ready)

        payload = {
            TXN_TYPE: XFER_PUBLIC,
            OUTPUTS: outputs_ready,
            INPUTS: inputs_ready,
            EXTRA: extra,
            SIGS: payment_signatures
        }

        request = Request(
            reqId=Request.gen_req_id(),
            operation=payload,
            protocolVersion=CURRENT_PROTOCOL_VERSION,
            identifier=address_to_verkey(first_address)
        )

        return request

    def _payment_signatures(self, inputs, outputs):
        signatures = []
        for [address, seq_no] in inputs:
            to_sign = [[[address.address, seq_no]], outputs]
            signature = address.signer.sign(to_sign)
            signatures.append(signature)
        return signatures
