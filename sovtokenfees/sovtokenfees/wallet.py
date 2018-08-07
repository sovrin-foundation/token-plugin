from typing import Tuple

from plenum.common.request import Request
from plenum.common.txn_util import get_seq_no
from plenum.common.types import f
from sovtokenfees.constants import FEES
from sovtoken.constants import INPUTS, OUTPUTS
from sovtoken.wallet import TokenWallet


class FeeSupportedWallet(TokenWallet):
    def add_fees_to_request(self, req: Request, fee_amount=None,
                            paying_utxo: Tuple=None, address=None,
                            change_address=None):
        if paying_utxo:
            address = paying_utxo[0]
            seq_no = paying_utxo[1]
            val = self.get_val(address, seq_no)
            assert val >= fee_amount
        else:
            if fee_amount is None:
                # TODO
                raise NotImplementedError
            else:
                utxo = self.get_min_utxo_ge(amount=fee_amount, address=address)
                assert utxo, 'No utxo to pay {}'.format(fee_amount)
                address, seq_no, val = utxo

        change_val = val - fee_amount
        if change_val > 0:
            if change_address is None:
                change_address = address
            outputs = [[change_address, change_val], ]
        else:
            outputs = []
        fees = self.get_fees([[address, seq_no], ],
                             outputs, req.digest)
        req.__setattr__(f.FEES.nm, fees)
        return req

    def get_fees(self, inputs, outputs, digest):
        fees = [[], outputs, []]
        for addr, seq_no in inputs:
            to_sign = [[addr, seq_no], outputs, digest]
            sig = self.addresses[addr].signer.sign(to_sign)
            fees[0].append([addr, seq_no])
            fees[-1].append(sig)
        return fees

    def on_reply_from_network(self, observer_name, req_id, frm, result,
                              num_replies):
        if FEES in result:
            self._update_inputs(result[FEES]['txn']['data'][INPUTS])
            self._update_outputs(result[FEES]['txn']['data'][OUTPUTS], get_seq_no(result[FEES]))
        super().on_reply_from_network(observer_name, req_id, frm, result,
                                      num_replies)
