from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import InvalidClientRequest
from plenum.common.request import Request

from sovtoken.constants import MINT_PUBLIC, XFER_PUBLIC, GET_UTXO, ACCEPTABLE_TXN_TYPES
from sovtoken.messages.txn_validator import txn_mint_public_validate, txn_xfer_public_validate, txt_get_utxo_validate

TXN_STATIC_VALIDATION_MAP = {
    MINT_PUBLIC: txn_mint_public_validate,
    XFER_PUBLIC: txn_xfer_public_validate,
    GET_UTXO: txt_get_utxo_validate
}


def static_req_validation(request: Request):
    if not isinstance(request, Request):
        raise InvalidClientRequest(None, None, "Invalid request - was not Request type")

    operation = request.operation
    txn_type = operation.get(TXN_TYPE)
    if txn_type in ACCEPTABLE_TXN_TYPES:

        static_validation_func = TXN_STATIC_VALIDATION_MAP[txn_type]
        error = static_validation_func(request)

        if error:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       error)
    else:
        raise InvalidClientRequest(request.identifier,
                                   request.reqId,
                                   "Invalid type in operation",
                                   txn_type)



