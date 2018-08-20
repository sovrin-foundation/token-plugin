from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import InvalidClientRequest
from plenum.common.types import PLUGIN_TYPE_AUTHENTICATOR, OPERATION, f
from plenum.common.verifier import DidVerifier
from plenum.server.client_authn import CoreAuthNr
from sovtokenfees import AcceptableWriteTypes, AcceptableQueryTypes
from sovtokenfees.constants import SET_FEES
from sovtoken.constants import INPUTS, OUTPUTS, SIGS
from sovtoken.client_authnr import AddressSigVerifier, TokenAuthNr


class FeesAuthNr(CoreAuthNr):
    pluginType = PLUGIN_TYPE_AUTHENTICATOR

    write_types = AcceptableWriteTypes
    query_types = AcceptableQueryTypes

    def __init__(self, state, token_authnr):
        super().__init__(state)
        self.token_authnr = token_authnr

    # ------------------------------------------------------------------------------------
    # verifies the request operation is transaction type of fees
    #       if transaction type is not fees, an exception is raised.
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

        digest = msg.digest
        return TokenAuthNr.verify_signtures_on_payments(fees[INPUTS], fees[OUTPUTS], fees[SIGS],
                                                        AddressSigVerifier, digest)

