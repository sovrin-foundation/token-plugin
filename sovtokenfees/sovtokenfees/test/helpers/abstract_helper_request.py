import json

from indy.payment import add_request_fees
from plenum.common.constants import TXN_TYPE
from sovtokenfees.constants import SET_FEES, FEES, GET_FEES
from sovtoken.constants import AMOUNT, ADDRESS

from stp_core.common.log import getlogger

logger = getlogger()


class AbstractHelperRequest:
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
                outputs.append({ADDRESS: address, AMOUNT: change_part+change_mod})
                change_mod = 0 # Only add remainder once
        else:
            outputs = []

        logger.info("*"*20)
        logger.info(str(outputs))

        request = self.add_fees_specific(request, inputs, outputs)

        return request

    def add_fees_specific(self, request, inputs, outputs):
        """
        Sign the fees and add them to a request.
        """
        inputs = self._prepare_inputs(inputs)
        outputs = self._prepare_outputs(outputs)

        request = self.add_fees_to_req(request, inputs, outputs)

        return request

    def add_fees_to_req(self, request, inputs, outputs):
        pass

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
