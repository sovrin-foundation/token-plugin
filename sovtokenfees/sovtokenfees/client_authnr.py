import base58

from common.serializers.serialization import serialize_msg_for_signing
from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import InvalidSignatureFormat, \
    InsufficientCorrectSignatures, InvalidClientRequest
from plenum.common.types import PLUGIN_TYPE_AUTHENTICATOR, OPERATION, f
from plenum.common.verifier import DidVerifier
from plenum.server.client_authn import CoreAuthNr
from sovtokenfees import AcceptableWriteTypes, AcceptableQueryTypes
from sovtokenfees.constants import SET_FEES, FEES
from sovtoken.client_authnr import AddressSigVerifier
from sovtoken.util import address_to_verkey


class FeesAuthNr(CoreAuthNr):
    pluginType = PLUGIN_TYPE_AUTHENTICATOR

    write_types = AcceptableWriteTypes
    query_types = AcceptableQueryTypes

    def __init__(self, state, token_authnr):
        super().__init__(state)
        self.token_authnr = token_authnr

    def authenticate(self, req_data, identifier: str = None,
                     signature: str = None, verifier=None):
        txn_type = req_data[OPERATION][TXN_TYPE]
        if txn_type == SET_FEES:
            verifier = verifier or DidVerifier
            return super().authenticate(req_data, identifier, signature,
                                        verifier=verifier)
        else:

            raise InvalidClientRequest(req_data[f.REQ_ID.nm], identifier,
                                       "txn type is {} not {}".format(txn_type, SET_FEES))

    # ------------------------------------------------------------------------------------
    # verify the signatures in the fees section
    #
    #     if the signatures found do not match the signatures expected,
    #            an exception is thrown.
    #
    #     If everything is ok, nothing is returned
    #     If there is no fees, nothing is returned
    def verify_signature(self, msg):
        try:
            fees = getattr(msg, f.FEES.nm)
        except (AttributeError, KeyError):
            return

        correct_sigs_from = set()
        required_sigs_from = set()
        outputs = fees[1]
        digest = msg.digest

        for (addr, seq_no), sig in zip(fees[0], fees[2]):

            required_sigs_from.add(addr)

            try:
                sig = base58.b58decode(sig.encode())
            except Exception as ex:
                raise InvalidSignatureFormat from ex

            to_ser = [[addr, seq_no], outputs, digest]
            serz = serialize_msg_for_signing(to_ser)
            try:
                verkey = address_to_verkey(addr)
            except ValueError:
                continue

            verifier = AddressSigVerifier(verkey=verkey)
            if verifier.verify(sig, serz):
                correct_sigs_from.add(addr)

        if correct_sigs_from != required_sigs_from:
            raise InsufficientCorrectSignatures(len(correct_sigs_from),
                                                len(fees[0]))

