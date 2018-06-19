from copy import deepcopy

import base58
from base58 import b58decode

from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import InsufficientCorrectSignatures, \
    CouldNotAuthenticate, InvalidSignatureFormat
from plenum.common.types import PLUGIN_TYPE_AUTHENTICATOR, OPERATION, f
from plenum.common.verifier import Verifier, DidVerifier
from plenum.server.client_authn import CoreAuthNr
from plenum.server.plugin.token.src import AcceptableWriteTypes, AcceptableQueryTypes
from plenum.server.plugin.token.src.constants import MINT_PUBLIC, XFER_PUBLIC, INPUTS, SIGS
from plenum.server.plugin.token.src.util import address_to_verkey
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

    def authenticate(self, req_data, identifier: str = None,
                     signature: str = None, verifier=None):
        if req_data[OPERATION][TXN_TYPE] == MINT_PUBLIC:
            verifier = verifier or DidVerifier
            return super().authenticate(req_data, identifier, signature,
                                        verifier=verifier)
        if req_data[OPERATION][TXN_TYPE] == XFER_PUBLIC:
            verifier = verifier or AddressSigVerifier
            return self.authenticate_xfer(req_data, verifier=verifier)

    def authenticate_xfer(self, req_data, verifier):
        new_data = {
            f.REQ_ID.nm: req_data[f.REQ_ID.nm],
            OPERATION: {k: deepcopy(req_data[OPERATION][k]) for k in req_data[OPERATION] if k != SIGS}
        }
        correct_sigs_from = []
        for inp, sig in zip(req_data[OPERATION][INPUTS],
                            req_data[OPERATION][SIGS]):
            try:
                sig = base58.b58decode(sig)
            except Exception as ex:
                raise InvalidSignatureFormat from ex

            new_data[OPERATION][INPUTS] = [inp, ]
            idr = inp[0]
            ser = super().serializeForSig(new_data, identifier=idr,
                                          topLevelKeysToIgnore=self.excluded_from_signing)
            verkey = self.getVerkey(idr)

            if verkey is None:
                raise CouldNotAuthenticate(
                    'Can not find verkey for {}'.format(idr))

            vr = verifier(verkey)
            if vr.verify(sig, ser):
                correct_sigs_from.append(idr)

        if len(correct_sigs_from) != len(req_data[OPERATION][INPUTS]):
            # All inputs should have signatures present
            raise InsufficientCorrectSignatures(len(correct_sigs_from),
                                                len(req_data[OPERATION][INPUTS]))
        return correct_sigs_from

    # def serializeForSig(self, msg, identifier=None, topLevelKeysToIgnore=None):
    #     if msg[OPERATION][TXN_TYPE] == MINT_PUBLIC:
    #         return super().serializeForSig(msg, identifier=identifier,
    #                                        topLevelKeysToIgnore=topLevelKeysToIgnore)
    #     if msg[OPERATION][TXN_TYPE] == XFER_PUBLIC:
    #         msg = self._get_xfer_ser_data(msg, identifier)
    #         return super().serializeForSig(msg, identifier=identifier,
    #                                        topLevelKeysToIgnore=topLevelKeysToIgnore)

    def getVerkey(self, identifier):
        if len(identifier) not in (21, 22):
            vk = address_to_verkey(identifier)
            if len(vk) in (43, 44):
            # Address is the 32 byte verkey
                return vk
        return super().getVerkey(identifier)

    # @staticmethod
    # def _get_xfer_ser_data(req_data, identifier):
    #     new_data = deepcopy(req_data)
    #     new_data.pop(f.IDENTIFIER.nm, None)
    #     new_data[OPERATION][INPUTS] = [i for i in new_data[OPERATION][INPUTS]
    #                                    if i[0] == identifier]
    #     return new_data
