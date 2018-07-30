import json
from random import randint

import pytest

from plenum.common.txn_util import get_seq_no
from sovtoken.constants import OUTPUTS
from sovtoken.util import update_token_wallet_with_result
from sovtoken.test.helper import send_xfer, send_get_utxo

from plenum.common.exceptions import RequestNackedException
from plenum.common.txn_util import get_seq_no
from plenum.common.types import OPERATION
from sovtoken.constants import INPUTS, SIGS
from sovtoken.util import update_token_wallet_with_result
from sovtoken.wallet import Address
from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies
from sovtoken.test.helper import xfer_request, \
    inputs_outputs, send_xfer


from sovtoken.test.helper import \
    user1_address, user1_token_wallet, user2_address, user2_token_wallet, \
    user3_address, user3_token_wallet

def test_multiple_inputs_with_1_incorrect_input_sig(tokens_distributed, # noqa
                                                    looper,
                                                    sdk_pool_handle,
                                                    seller_address,
                                                    user1_token_wallet,
                                                    user2_token_wallet,
                                                    user3_token_wallet):
    # Multiple inputs are used in a transaction but one of the inputs
    # has incorrect signature
    inputs, outputs = inputs_outputs(user1_token_wallet, user2_token_wallet,
                                     user3_token_wallet,
                                     output_addr=seller_address)

    request = xfer_request(inputs, outputs)
    operation = getattr(request, OPERATION)
    # Change signature for 2nd input, set it same as the 1st input's signature
    operation[SIGS][1] = operation[SIGS][0]
    reqs = sdk_send_signed_requests(sdk_pool_handle,
                                    [json.dumps(request.as_dict), ])
    with pytest.raises(RequestNackedException):
        sdk_get_and_check_replies(looper, reqs)


def test_multiple_inputs_with_1_missing_sig(tokens_distributed, # noqa
                                            looper,
                                            sdk_pool_handle,
                                            seller_address,
                                            user1_token_wallet,
                                            user2_token_wallet,
                                            user3_token_wallet,
                                            seller_token_wallet):
    # Multiple inputs are used in a transaction but one of the inputs's
    # signature is missing, 2 cases are checked, in 1st case one of the input's
    # signature is removed from the request so there are 3 inputs but only 2
    # signatures, in 2nd case one of the inputs signature is still not included
    #  but a different input's signature is added which is not being spent in
    # this txn, so there are 3 inputs and 3 signtures.
    inputs, outputs = inputs_outputs(user1_token_wallet, user2_token_wallet,
                                     user3_token_wallet,
                                     output_addr=seller_address)

    # Remove signature for 2nd input
    request = xfer_request(inputs, outputs)
    request.operation[SIGS].pop()
    assert len(request.operation[SIGS]) == (len(inputs) - 1)
    reqs = sdk_send_signed_requests(sdk_pool_handle,
                                    [json.dumps(request.as_dict), ])
    with pytest.raises(RequestNackedException):
        sdk_get_and_check_replies(looper, reqs)

    # Add signature from an address not present in input
    seq_no, _ = next(iter(
        seller_token_wallet.get_all_address_utxos(seller_address).values()))[0]
    seller_token_wallet.sign_using_output(seller_address, seq_no,
                                          request=request)
    assert len(request.operation[SIGS]) == len(inputs)
    reqs = sdk_send_signed_requests(sdk_pool_handle,
                                    [json.dumps(request.as_dict), ])
    with pytest.raises(RequestNackedException):
        sdk_get_and_check_replies(looper, reqs)


@pytest.fixture(scope='module')
def added_addresses(user1_token_wallet, user2_token_wallet, user3_token_wallet):
    addr1 = Address()
    user1_token_wallet.add_new_address(addr1)
    addr2 = Address()
    user2_token_wallet.add_new_address(addr2)
    addr3 = Address()
    user3_token_wallet.add_new_address(addr3)
    return addr1.address, addr2.address, addr3.address


def get_3_random_parts(total):
    # Divide `total` in 3 random parts
    part1, part2 = randint(1, total // 2), randint(1, total // 2)
    part3 = total - (part1 + part2)
    return part1, part2, part3


@pytest.fixture(scope='module')
def first_xfer_done(tokens_distributed, # noqa
                    looper,
                    sdk_pool_handle,
                    user1_token_wallet,
                    user2_token_wallet,
                    user3_token_wallet,
                    user1_address,
                    user2_address,
                    user3_address,
                    added_addresses):
    xfer_seq_no = tokens_distributed
    inputs = [[user1_token_wallet, user1_address, xfer_seq_no],
              [user2_token_wallet, user2_address, xfer_seq_no],
              [user3_token_wallet, user3_address, xfer_seq_no]]

    # Each address will just have 1 unspent sequence number
    output_val = sum([w.get_total_address_amount(address=a) for (w, a) in [
        (user1_token_wallet, user1_address),
        (user2_token_wallet, user2_address),
        (user3_token_wallet, user3_address)]])

    part1, part2, part3 = get_3_random_parts(output_val)
    addr1, addr2, addr3 = added_addresses
    outputs = [[addr1, part1], [addr2, part2], [addr3, part3]]
    result = send_xfer(looper, inputs, outputs, sdk_pool_handle)
    for w in [user1_token_wallet, user2_token_wallet, user3_token_wallet]:
        update_token_wallet_with_result(w, result)
    return get_seq_no(result)


def test_multiple_inputs_outputs_without_change(first_xfer_done,
                                                user1_token_wallet,
                                                user2_token_wallet,
                                                user3_token_wallet,
                                                user1_address,
                                                user2_address,
                                                user3_address):
    # Transfer with multiple inputs and outputs but with no change (input and
    # output addresses are mutually exclusive)
    assert user1_token_wallet.get_total_address_amount(user1_address) == 0
    assert user2_token_wallet.get_total_address_amount(user2_address) == 0
    assert user3_token_wallet.get_total_address_amount(user3_address) == 0


def test_multiple_inputs_outputs_with_change(first_xfer_done,
                                             looper,
                                             sdk_pool_handle,
                                             user1_token_wallet,
                                             user2_token_wallet,
                                             user3_token_wallet,
                                             added_addresses):
    xfer_seq_no = first_xfer_done
    addr1, addr2, addr3 = added_addresses
    inputs = [[user1_token_wallet, addr1, xfer_seq_no],
              [user2_token_wallet, addr2, xfer_seq_no],
              [user3_token_wallet, addr3, xfer_seq_no]]
    # Each address will just have 1 unspent sequence number
    output_val = sum([w.get_total_address_amount(address=a) for (w, a) in [
        (user1_token_wallet, addr1),
        (user2_token_wallet, addr2),
        (user3_token_wallet, addr3)]])

    part1, part2, part3 = get_3_random_parts(output_val)
    # Create 2 new addresses but for the `user3` use his old address
    new_addr1 = Address()
    user1_token_wallet.add_new_address(new_addr1)
    new_addr2 = Address()
    user2_token_wallet.add_new_address(new_addr2)
    outputs = [[new_addr1.address, part1], [new_addr2.address, part2],
               [addr3, part3]]
    result = send_xfer(looper, inputs, outputs, sdk_pool_handle)
    for w in [user1_token_wallet, user2_token_wallet, user3_token_wallet]:
        update_token_wallet_with_result(w, result)
    assert user1_token_wallet.get_total_address_amount(addr1) == 0
    assert user2_token_wallet.get_total_address_amount(addr2) == 0
    assert user3_token_wallet.get_total_address_amount(addr3) == part3
