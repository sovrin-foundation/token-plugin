from sovtoken.constants import ADDRESS
from sovtoken.test.helpers import HelperInnerRequest
from sovtokenfees.constants import FEES, SET_FEES, GET_FEES
from sovtokenfees.test.helpers.abstract_helper_request import AbstractHelperRequest

from plenum.common.constants import TXN_TYPE
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

    def set_fees(self, fees):
        """ Build a request to set the fees. """
        payload = {
            TXN_TYPE: SET_FEES,
            FEES: fees,
        }

        request = self._create_request(payload)
        request = self._wallet.sign_request_trustees(request, number_signers=3)
        return request

    def get_fees(self):
        """ Build a request to get the fees. """
        payload = {
            TXN_TYPE: GET_FEES
        }

        request = self._create_request(payload, identifier=self._client_did)
        return request

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

    def inject_fees_specific(self, request, inputs, outputs):
        """
        Sign the fees and add them to a request.
        """
        fees_signatures = self.fees_signatures(inputs, outputs, request.payload_digest)

        fees = [inputs, outputs, fees_signatures]
        setattr(request, FEES, fees)

        return request
