from plenum.common.constants import TXN_TYPE
from plenum.common.exceptions import InvalidClientRequest
from plenum.common.messages.fields import IterableField
from plenum.common.request import Request

from sovtoken.constants import MINT_PUBLIC, XFER_PUBLIC, GET_UTXO, INPUTS, SIGS, ADDRESS, OUTPUTS
from sovtoken.messages.fields import PublicOutputField, PublicOutputsField, PublicInputsField

PUBLIC_OUTPUT_VALIDATOR = IterableField(PublicOutputField())
PUBLIC_OUTPUTS_VALIDATOR = PublicOutputsField()
PUBLIC_INPUTS_VALIDATOR = PublicInputsField()


def outputs_validate(request: Request):
    operation = request.operation
    if OUTPUTS not in operation:
        raise InvalidClientRequest(request.identifier, request.reqId,
                                   "{} needs to be present".
                                   format(OUTPUTS))
    return PUBLIC_OUTPUTS_VALIDATOR.validate(operation[OUTPUTS])


def inputs_validate(request: Request):
    operation = request.operation
    if INPUTS not in operation:
        raise InvalidClientRequest(request.identifier,
                                   request.reqId,
                                   "{} needs to be present".
                                   format(INPUTS))
    if SIGS not in operation:
        raise InvalidClientRequest(request.identifier,
                                   request.reqId,
                                   "{} needs to be present".
                                   format(SIGS))
    # THIS IS TEMPORARY. The new format of requests will take an array of signatures
    if len(operation[INPUTS]) != len(operation[SIGS]):
        raise InvalidClientRequest(request.identifier,
                                   request.reqId,
                                   "all inputs should have signatures")
    return PUBLIC_INPUTS_VALIDATOR.validate(operation[INPUTS])


def address_validate(request: Request):
    operation = request.operation
    if ADDRESS not in operation:
        error = '{} needs to be provided'.format(ADDRESS)
    else:
        error = PUBLIC_OUTPUT_VALIDATOR.inner_field_type.public_address_field.validate(operation[ADDRESS])
    if error:
        raise InvalidClientRequest(request.identifier,
                                   request.reqId, error)


def txn_mint_public_validate(request: Request):
    operation = request.operation
    if operation[TXN_TYPE] == MINT_PUBLIC:
        return outputs_validate(request)


def txn_xfer_public_validate(request: Request):
    operation = request.operation
    if operation[TXN_TYPE] == XFER_PUBLIC:
        error = outputs_validate(request)
        if error:
            return error
        else:
            error = inputs_validate(request)
        return error


def txt_get_utxo_validate(request: Request):
    operation = request.operation
    if operation[TXN_TYPE] == GET_UTXO:
        return address_validate(request)
