from plenum.common.constants import TXN_TYPE
from sovtoken.constants import INPUTS, OUTPUTS, EXTRA, SIGS, XFER_PUBLIC
from sovtoken.util import address_to_verkey


class HelperRequests():
    """
    Helper to build different requests.

    # methods
    - transfer
    """

    def transfer(self, wallet, inputs, outputs, extra=None):
        """ Builds a transfer request """
        payload = {
            TXN_TYPE: XFER_PUBLIC,
            OUTPUTS: outputs,
            INPUTS: inputs,
            EXTRA: extra,
            SIGS: []
        }

        first_address, seq_no = inputs[0][0]
        request = wallet.sign_using_output(first_address, seq_no, op=payload)
        request._identifier = address_to_verkey(first_address)
        request.operation[SIGS] = self._payment_signatures(
            wallet,
            inputs,
            outputs
        )

        return request

    def _payment_signatures(self, wallet, inputs, outputs):
        signatures = []
        for [address, seq_no] in inputs:
            to_sign = [[[address, seq_no]], outputs]
            signature = wallet.addresses[address].signer.sign(to_sign)
            signatures.append(signature)
        return signatures
