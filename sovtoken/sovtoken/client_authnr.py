from copy import deepcopy

import base58
from base58 import b58decode

from common.serializers.serialization import serialize_msg_for_signing
from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import (CouldNotAuthenticate,
                                      InsufficientCorrectSignatures,
                                      InvalidSignatureFormat)
from plenum.common.types import OPERATION, PLUGIN_TYPE_AUTHENTICATOR, f
from plenum.common.verifier import DidVerifier, Verifier
from plenum.server.client_authn import CoreAuthNr
from sovtoken import AcceptableQueryTypes, AcceptableWriteTypes
from sovtoken.constants import (ADDRESS, INPUTS, MINT_PUBLIC, OUTPUTS, SIGS,
                                XFER_PUBLIC, EXTRA)
from sovtoken.util import address_to_verkey
from stp_core.crypto.nacl_wrappers import Verifier as NaclVerifier


class AddressSigVerifier(Verifier):
    def __init__(self, verkey, **kwargs):
        self.verkey = verkey
        self._vr = NaclVerifier(b58decode(verkey))

    def verify(self, sig, msg) -> bool:
        return self._vr.verify(sig, msg)


class TokenAuthNr(CoreAuthNr):
    pluginType = PLUGIN_TYPE_AUTHENTICATOR

    write_types = AcceptableWriteTypes
    query_types = AcceptableQueryTypes

    # ------------------------------------------------------------------------------------
    # Entrance point for transaction signature verification. Here come all transactions of all types,
    # but only XFER_PUBLIC and MINT_PUBLIC are verified
    def authenticate(self, req_data, identifier: str = None,
                     signature: str = None, verifier=None):
        if req_data[OPERATION][TXN_TYPE] == MINT_PUBLIC:
            verifier = verifier or DidVerifier
            return super().authenticate(req_data, identifier, signature,
                                        verifier=verifier)
        if req_data[OPERATION][TXN_TYPE] == XFER_PUBLIC:
            verifier = verifier or AddressSigVerifier
            return self.authenticate_xfer(req_data, verifier=verifier)

    # ------------------------------------------------------------------------------------
    # Signature authentication for XFER
    # It checks the signatures for array of one input and all outputs with a key from input
    # If the check fails, it will raise InsufficientCorrectSignatures
    # The verkey will be unobtainable from input, it will raise CouldNotAuthenticate
    # Raises UnknownIdentifier if input is not a valid base58 value
    def authenticate_xfer(self, req_data, verifier):
        extra_fields = []
        if req_data[OPERATION].get(EXTRA, None):
            extra_fields.append(req_data[OPERATION][EXTRA])
        if req_data.get(f.TAA_ACCEPTANCE.nm, None):
            extra_fields.append(req_data[f.TAA_ACCEPTANCE.nm])
        return self.verify_signtures_on_payments(req_data[OPERATION][INPUTS],
                                                 req_data[OPERATION][OUTPUTS],
                                                 req_data[OPERATION][SIGS],
                                                 verifier,
                                                 *extra_fields)

    # ------------------------------------------------------------------------------------
    # Gets verkey from payment address
    # Raises UnknownIdentifier if it is not a valid base58 value
    def getVerkey(self, identifier):
        if len(identifier) not in (21, 22):
            vk = address_to_verkey(identifier)
            if len(vk) in (43, 44):
            # Address is the 32 byte verkey
                return vk
        return super().getVerkey(identifier)

    @staticmethod
    def verify_signtures_on_payments(inputs, outputs, signatures, verifier,
                                     *extra_fields_for_signing):
        correct_sigs_from = []
        for inp, sig in zip(inputs,
                            signatures):
            try:
                sig = base58.b58decode(sig)
            except Exception as ex:
                raise InvalidSignatureFormat from ex

            # TODO: Account for `extra` field
            new_data = [inp, outputs]
            new_data.extend(extra_fields_for_signing)
            idr = inp[ADDRESS]
            ser = serialize_msg_for_signing(new_data)
            try:
                verkey = address_to_verkey(idr)
            except ValueError:
                continue

            vr = verifier(verkey)
            if vr.verify(sig, ser):
                correct_sigs_from.append(idr)

        if len(correct_sigs_from) != len(inputs):
            # All inputs should have signatures present
            raise InsufficientCorrectSignatures(len(correct_sigs_from),
                                                len(inputs))
        return correct_sigs_from
