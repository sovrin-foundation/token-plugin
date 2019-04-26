from sovtoken.constants import ADDRESS
from sovtoken.test.helpers import HelperInnerRequest
from sovtokenfees.constants import FEES
from sovtokenfees.test.helpers.abstract_helper_request import AbstractHelperRequest

from stp_core.common.log import getlogger

logger = getlogger()


class HelperInnerRequest(AbstractHelperRequest, HelperInnerRequest):
    """
    Extends the sovtoken HelperRequest with fee related requests.

    # Methods
    - set_fees
    - get_fees
    - add_fees
    - add_fees_specific
    - find_utxos_can_pay
    - fees_signatures
    """

    def fees_signatures(self, inputs, outputs, digest):
        """ Sign the fees for a non transfer request. This method is used only in inner version of wall"""
        signatures = []
        inputs = self._prepare_inputs(inputs)
        outputs = self._prepare_outputs(outputs)

        for utxo in inputs:
            address = utxo[ADDRESS]
            signer = self._wallet.get_address_instance(address).signer
            to_sign = [utxo, outputs, digest]
            sig = signer.sign(to_sign)
            signatures.append(sig)

        return signatures

    def add_fees_to_req(self, request, inputs, outputs):
        fees_signatures = self.fees_signatures(inputs, outputs, request.payload_digest)

        fees = [inputs, outputs, fees_signatures]
        setattr(request, FEES, fees)
        return request
