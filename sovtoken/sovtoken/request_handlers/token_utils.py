from typing import Optional, List

from sovtoken.constants import INPUTS, OUTPUTS
from sovtoken.exceptions import UTXOError, InvalidFundsError, ExtraFundsError, InsufficientFundsError
from sovtoken.types import Output
from sovtoken.utxo_cache import UTXOCache

from plenum.common.exceptions import InvalidClientMessageException
from plenum.common.request import Request
from plenum.common.types import f


def spend_input(state, utxo_cache: UTXOCache, address, seq_no, is_committed=False):
    state_key = create_state_key(address, seq_no)
    state.set(state_key, b'')
    utxo_cache.spend_output(Output(address, seq_no, None),
                            is_committed=is_committed)


def add_new_output(state, utxo_cache: UTXOCache, output: Output, is_committed=False):
    address = output.address
    seq_no = output.seqNo
    amount = output.amount
    state_key = create_state_key(address, seq_no)
    state.set(state_key, str(amount).encode())
    utxo_cache.add_output(output, is_committed=is_committed)


def create_state_key(address: str, seq_no: int) -> bytes:
    return ':'.join([address, str(seq_no)]).encode()


def parse_state_key(key: str) -> List[str]:
    return key.split(':')


def sum_inputs(utxo_cache: UTXOCache, request: Request, is_committed=False) -> int:
    try:
        inputs = request.operation[INPUTS]
        return utxo_cache.sum_inputs(inputs, is_committed=is_committed)
    except UTXOError as ex:
        raise InvalidFundsError(request.identifier, request.reqId, '{}'.format(ex))


def sum_outputs(request: Request) -> int:
    return sum(o["amount"] for o in request.operation[OUTPUTS])


def validate_given_inputs_outputs(inputs_sum, outputs_sum, required_amount, request,
                                  error_msg_suffix: Optional[str] = None):
    """
    Checks three sum values against simple set of rules. inputs_sum must be equal to required_amount. Exceptions
    are raise if it is not equal. The outputs_sum is pass not for checks but to be included in error messages.
    This is confusing but is required in cases where the required amount is different then the sum of outputs (
    in the case of fees).

    :param inputs_sum: the sum of inputs
    :param outputs_sum: the sum of outputs
    :param required_amount: the required amount to validate (could be equal to output_sum, but may be different)
    :param request: the request that is being validated
    :param error_msg_suffix: added message to the error message
    :return: returns if valid or will raise an exception
    """

    if inputs_sum == required_amount:
        return  # Equal is valid
    elif inputs_sum > required_amount:
        error = 'Extra funds, sum of inputs is {} ' \
                'but required amount: {} -- sum of outputs: {}'.format(inputs_sum, required_amount, outputs_sum)
        if error_msg_suffix and isinstance(error_msg_suffix, str):
            error += ' ' + error_msg_suffix
        raise ExtraFundsError(getattr(request, f.IDENTIFIER.nm, None),
                              getattr(request, f.REQ_ID.nm, None),
                              error)

    elif inputs_sum < required_amount:
        error = 'Insufficient funds, sum of inputs is {}' \
                'but required amount is {}. sum of outputs: {}'.format(inputs_sum, required_amount, outputs_sum)
        if error_msg_suffix and isinstance(error_msg_suffix, str):
            error += ' ' + error_msg_suffix
        raise InsufficientFundsError(getattr(request, f.IDENTIFIER.nm, None),
                                     getattr(request, f.REQ_ID.nm, None),
                                     error)

    raise InvalidClientMessageException(getattr(request, f.IDENTIFIER.nm, None),
                                        getattr(request, f.REQ_ID.nm, None),
                                        'Request to not meet minimum requirements')
