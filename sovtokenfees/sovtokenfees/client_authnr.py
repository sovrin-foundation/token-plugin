from indy_node.server.client_authn import LedgerBasedAuthNr
from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import InvalidClientRequest
from plenum.common.types import PLUGIN_TYPE_AUTHENTICATOR, OPERATION, f
from plenum.common.verifier import DidVerifier
from sovtokenfees.constants import SET_FEES
from sovtoken.client_authnr import AddressSigVerifier, TokenAuthNr

from plenum.common.messages.internal_messages import PreSigVerification


class FeesAuthNr(LedgerBasedAuthNr):
    PLUGIN_TYPE = PLUGIN_TYPE_AUTHENTICATOR

    def __init__(self, write_types, query_types, action_types, cache, token_authnr):
        super().__init__(write_types, query_types, action_types, cache)
        self.token_authnr = token_authnr

    def authenticate(self, req_data, identifier: str = None,
                     signature: str = None, verifier=None):
        """
        verifies the request operation is transaction type of fees
        if transaction type is not fees, an exception is raised.
        """
        txn_type = req_data[OPERATION][TXN_TYPE]
        if txn_type == SET_FEES:
            verifier = verifier or DidVerifier
            return super().authenticate(req_data, identifier, signature,
                                        verifier=verifier)
        else:

            raise InvalidClientRequest(req_data[f.REQ_ID.nm], identifier,
                                       "txn type is {} not {}".format(txn_type, SET_FEES))

    def verify_signature(self, msg: PreSigVerification):
        """
        verify the signatures in the fees section
        if the signatures found do not match the signatures expected,
               an exception is thrown.

        If everything is ok, nothing is returned
        If there is no fees, nothing is returned
        """
        msg = msg.cmsg
        try:
            fees = getattr(msg, f.FEES.nm)
        except (AttributeError, KeyError):
            return

        digest = msg.payload_digest
        return TokenAuthNr.verify_signtures_on_payments(fees[0], fees[1], fees[2],
                                                        AddressSigVerifier, digest)
