from copy import deepcopy
from tokens.src import AcceptableWriteTypes, AcceptableQueryTypes

from base58 import b58decode
from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import InsufficientCorrectSignatures
from plenum.common.types import PLUGIN_TYPE_AUTHENTICATOR, OPERATION
from plenum.common.verifier import Verifier, DidVerifier
from plenum.server.client_authn import CoreAuthNr
from stp_core.crypto.nacl_wrappers import Verifier as NaclVerifier

from tokens.src.constants import MINT_PUBLIC, XFER_PUBLIC, INPUTS


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
            correct_signers = super().authenticate(req_data, verifier=verifier)
            input_addrs = {addr for addr, _ in req_data[OPERATION][INPUTS]}
            missing_sigs_by = input_addrs.difference(set(correct_signers))
            # All inputs should have signatures present
            if missing_sigs_by:
                raise InsufficientCorrectSignatures(len(missing_sigs_by),
                                                    len(input_addrs))
            return correct_signers

    def serializeForSig(self, msg, identifier=None, topLevelKeysToIgnore=None):
        if msg[OPERATION][TXN_TYPE] == MINT_PUBLIC:
            return super().serializeForSig(msg, identifier=identifier,
                                           topLevelKeysToIgnore=topLevelKeysToIgnore)
        if msg[OPERATION][TXN_TYPE] == XFER_PUBLIC:
            msg = self._get_xfer_ser_data(msg, identifier)
            return super().serializeForSig(msg, identifier=identifier,
                                           topLevelKeysToIgnore=topLevelKeysToIgnore)

    def getVerkey(self, identifier):
        if len(identifier) in (43, 44):
            # Address is the 32 byte verkey
            return identifier
        return super().getVerkey(identifier)

    @staticmethod
    def _get_xfer_ser_data(req_data, identifier):
        new_data = deepcopy(req_data)
        new_data[OPERATION][INPUTS] = [i for i in new_data[OPERATION][INPUTS]
                                       if i[0] == identifier]
        return new_data
