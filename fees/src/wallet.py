from typing import Tuple

from plenum.common.request import Request
from plenum.common.types import f
from plenum.server.plugin.token.src.wallet import TokenWallet


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

        if change_address is None:
            change_address = address

        change_val = val - fee_amount
        fees = self.get_fees([[address, seq_no], ],
                             [[change_address, change_val], ])
        req.__setattr__(f.FEES.nm, fees)
        # for addr, sig in sigs.items():
        #     req.add_signature(addr, sig)
        return req

    def get_fees(self, inputs, outputs):
        fees = [[], outputs]
        for addr, seq_no in inputs:
            to_sign = [[addr, seq_no], outputs]
            sig = self.addresses[addr].signer.sign(to_sign)
            fees[0].append([addr, seq_no, sig])
        return fees
