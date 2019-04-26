from collections import OrderedDict
from copy import deepcopy
from typing import Dict, Optional, Tuple

import math
import base58

from ledger.util import F
from plenum.client.wallet import Wallet
from plenum.common.constants import TXN_TYPE, CURRENT_PROTOCOL_VERSION
from plenum.common.did_method import DidMethods
from plenum.common.messages.fields import TxnSeqNoField
from plenum.common.request import Request
from plenum.common.signer_simple import SimpleSigner
from plenum.common.txn_util import get_type, get_payload_data, get_seq_no
from plenum.common.types import OPERATION, f
from plenum.common.util import lxor
from sovtoken.constants import INPUTS, GET_UTXO, OUTPUTS, XFER_PUBLIC, SIGS


class Address:
    def __init__(self, seed=None):
        self.signer = SimpleSigner(seed=seed)
        self.address = base58.b58encode_check(self.signer.naclSigner.verraw).decode()
        self.outputs = [OrderedDict(), OrderedDict()]  # Unspent and Spent

    # TODO ST-525 test
    def amount(self, seq_no):
        return self.outputs[0].get(seq_no, self.outputs[1].get(seq_no))

    def is_unspent(self, seq_no):
        return seq_no in self.outputs[0]

    def spent(self, seq_no):
        val = self.outputs[0].pop(seq_no, None)
        if val:
            self.outputs[1][seq_no] = val

    def add_utxo(self, seq_no, val):
        self.outputs[0][seq_no] = val

    @property
    def verkey(self) -> str:
        return self.signer.verkey

    # TODO ST-525 test
    @property
    def all_utxos(self):
        return list(self.outputs[0].items())

    # TODO ST-525 test
    @property
    def all_seq_nos(self):
        return list(self.outputs[0])

    @property
    def total_amount(self):
        return sum(v for v in self.outputs[0].values())


class TokenWallet(Wallet):
    txn_seq_no_valdator = TxnSeqNoField()

    def __init__(self,
                 name: str=None,
                 supportedDidMethods: DidMethods=None):
        super().__init__(name, supportedDidMethods)
        self.addresses = OrderedDict()  # type: OrderedDict[str, Address]
        self.reply_handlers = {
            GET_UTXO: self.handle_get_utxo_response,
            XFER_PUBLIC: self.handle_xfer
        }

    def add_new_address(self, address: Address=None, seed=None):
        assert address or seed
        if not address:
            address = Address(seed=seed)
        assert address.address not in self.addresses
        self.addresses[address.address] = address

    def sign_using_output(self, id, seq_no, op: Dict=None,
                          request: Request=None):
        assert lxor(op, request)
        if op:
            request = Request(reqId=Request.gen_req_id(), operation=op, protocolVersion=CURRENT_PROTOCOL_VERSION)
        # existing_inputs = request.operation.get(INPUTS, [])
        # request.operation[INPUTS] = [[id, seq_no], ]
        # payload = deepcopy(request.signingState(id))
        # # TEMPORARY
        # payload[OPERATION].pop(SIGS)
        # payload.pop(f.IDENTIFIER.nm)
        #
        # signature = self.addresses[id].signer.sign(payload)
        # request.operation[INPUTS] = existing_inputs + [[id, seq_no], ]
        # TODO: Account for `extra` field
        payload = [[{"address": id, "seqNo": seq_no}, ], request.operation[OUTPUTS]]
        signature = self.addresses[id].signer.sign(payload)
        request.operation[INPUTS] = request.operation.get(INPUTS, []) + [{"address": id, "seqNo": seq_no}, ]
        request.operation[SIGS].append(signature)
        return request

    def get_all_wallet_utxos(self):
        return {address: address.all_utxos
                for address in self.addresses.values()}

    def get_all_address_utxos(self, address):
        if address in self.addresses:
            return {self.addresses[address]: self.addresses[address].all_utxos}
        else:
            return {}

    def get_total_wallet_amount(self):
        return sum(addr.total_amount for addr in self.addresses.values())

    def get_total_address_amount(self, address):
        if address in self.addresses:
            return self.addresses[address].total_amount
        else:
            return 0

    def on_reply_from_network(self, observer_name, req_id, frm, result,
                              num_replies):
        try:
            typ = get_type(result)
        except KeyError:
            # For queries
            typ = result[TXN_TYPE]
        if typ and typ in self.reply_handlers:
            self.reply_handlers[typ](result)

    def handle_get_utxo_response(self, response):
        self._update_outputs(response[OUTPUTS])

    def handle_xfer(self, response):
        data = get_payload_data(response)
        seq_no = get_seq_no(response)
        self._update_inputs(data[INPUTS])
        self._update_outputs(data[OUTPUTS], seq_no)

    def _update_inputs(self, inputs):
        for inp in inputs:
            addr = inp["address"]
            seq_no = inp["seqNo"]
            if addr in self.addresses:
                self.addresses[addr].spent(seq_no)

    def _update_outputs(self, outputs, txn_seq_no=None):
        for output in outputs:
            try:
                addr = output["address"]
                val = output["amount"]
                try:
                    seq_no = output["seqNo"]
                except KeyError as ex:
                    if txn_seq_no and isinstance(txn_seq_no, int):
                        seq_no = txn_seq_no
                    else:
                        raise ex
            except Exception:
                raise ValueError('Cannot handle output {}'.format(output))
            if addr in self.addresses:
                self.addresses[addr].add_utxo(seq_no, val)

    def get_min_utxo_ge(self, amount, address=None) -> Optional[Tuple]:
        # Get minimum utxo greater than or equal to `amount`
        def get_address_utxos(address):
            for (seq_no, amount) in address.all_utxos:
                yield {"address": address.address, "seqNo": seq_no, "amount": amount}

        if address:
            all_utxos = get_address_utxos(self.addresses[address])
        else:
            all_utxos = [
                utxo
                for address in self.addresses.values()
                for utxo in get_address_utxos(address)
            ]

        filtered = filter(lambda utxo: utxo["amount"] >= amount, all_utxos)
        return min(filtered, key=lambda utxo: utxo["amount"], default=None)

    def get_val(self, address, seq_no):
        # Get value of unspent output (address and seq_no), can raise KeyError
        return self.addresses[address].outputs[0][seq_no]
