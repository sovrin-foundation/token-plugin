import sovtoken.test.helpers.helper_request as token_helper_request

from plenum.common.constants import TXN_TYPE
from sovtokenfees.constants import SET_FEES, FEES, GET_FEES
from sovtoken.constants import AMOUNT, ADDRESS

from stp_core.common.log import getlogger

logger = getlogger()


class HelperRequest(token_helper_request.HelperRequest):
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

        request = self._create_request(payload,
                                       identifier=self._wallet._trustee_wallets[0].defaultId)
        request = self._wallet.sign_request_trustees(request, number_signers=3)
        return request

    def get_fees(self):
        """ Build a request to get the fees. """
        payload = {
            TXN_TYPE: GET_FEES
        }

        request = self._create_request(payload, identifier=self._client_did)
        return request

    def add_fees(
        self,
        request,
        utxos,
        fee_amount,
        change_address=None
    ):
        """
        Add fees to a non transfer request.

        Will find utxos to cover the fee_amount. If it requires more than a
        single utxo to pay for the fees, it will use the smallest utxo and look
        again. If the utxos can't cover the cost, an exception will be thrown.
        """
        inputs = self.find_utxos_can_pay(utxos, fee_amount)
        total_inputs = sum(map(lambda utxo: utxo[AMOUNT], inputs))
        change = total_inputs - fee_amount

        if change > 0 and change_address:
            if not isinstance(change_address, list):
                change_address = [change_address]
            change_part = change // len(change_address)
            if change_part <= 0:
                raise Exception("Unable to divide {}, {} ways".format(change, len(change_address)))
            change_mod = change % len(change_address)
            outputs = []
            for address in change_address:
                outputs.append({ADDRESS: address, AMOUNT: change_part + change_mod})
                change_mod = 0  # Only add remainder once
        else:
            outputs = []

        logger.info("*" * 20)
        logger.info(str(outputs))

        request = self.add_fees_specific(request, inputs, outputs)
        return request

    def add_fees_specific(self, request, inputs, outputs):
        """
        Sign the fees and add them to a request.
        """
        inputs = self._prepare_inputs(inputs)
        outputs = self._prepare_outputs(outputs)

        return self.inject_fees_specific(request, inputs, outputs)


    def inject_fees_specific(self, request, inputs, outputs):
        """
        Sign the fees and add them to a request.
        """
        fees_signatures = self.fees_signatures(inputs, outputs, request.payload_digest)

        fees = [inputs, outputs, fees_signatures]
        setattr(request, FEES, fees)

        return request


    def find_utxos_can_pay(self, utxos, amount):
        """
        Return a list of utxos that can cover a cost.

        utxos are in the format of {
            "address" : "suaKoendzrJrwNEWWYnSJ5CM8dPAdAaur5Bp5BBVap8e1Ccdw",
            "seqNo": 3,
            "amount" 10000
        }

        If a utxo can't cover the amount, it will take the lowest utxo and
        then try again.
        """
        # Sort by amount, least to greatest
        utxos.sort(key=lambda utxo: utxo[AMOUNT])

        def _find_utxos(utxos, amount, utxos_to_pay=[]):
            if not utxos:
                raise Exception("UTXOs don't have enough to cover the cost.")

            for utxo in utxos:
                if utxo[AMOUNT] >= amount:
                    utxos_to_pay.append(utxo)
                    break
            # Executed if for loop is ran and no utxo is found equal to amount.
            # Will take the lowest utxo and run again.
            else:
                smallest = utxos.pop(0)
                utxos_to_pay.append(smallest)
                _find_utxos(utxos, amount - smallest[AMOUNT], utxos_to_pay)

            return utxos_to_pay

        return _find_utxos(utxos, amount)

    def fees_signatures(self, inputs, outputs, digest):
        """ Sign the fees for a non transfer request. """
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
