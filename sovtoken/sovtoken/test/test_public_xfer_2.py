import pytest
import json

from base58 import b58encode_check
from plenum.common.exceptions import RequestNackedException, \
    RequestRejectedException
from plenum.common.txn_util import get_seq_no
from plenum.common.util import lxor, randomString
from sovtoken.constants import OUTPUTS, ADDRESS, SEQNO, AMOUNT
from sovtoken.test.helper import check_output_val_on_all_nodes, \
    xfer_request, send_get_utxo
from sovtoken.test.conftest import seller_gets
from plenum.test.helper import sdk_send_signed_requests, \
    sdk_get_replies, sdk_check_reply
from sovtoken.test.helper import user1_token_wallet, user2_token_wallet, \
    user1_address, user2_address


@pytest.fixture
def addresses(helpers, user1_token_wallet):
    return helpers.wallet.add_new_addresses(user1_token_wallet, 2)


@pytest.fixture
def initial_mint(helpers, addresses):
    outputs = [{"address": address, "amount": 100} for address in addresses]
    return helpers.general.do_mint(outputs)


def test_seller_xfer_outputs_repeat_address(
    helpers,
    initial_mint,
    addresses,
):
    """
    Address repeats in the output of transaction, hence it will be rejected
    """
    seq_no = get_seq_no(initial_mint)
    [seller_address, user1_address] = addresses

    inputs = [{"address": seller_address, "seqNo": seq_no}]
    outputs = [
        {"address": user1_address, "amount": 10},
        {"address": seller_address, "amount": 45},
        {"address": seller_address, "amount": 45}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)


def test_seller_xfer_float_amount(
    helpers,
    initial_mint,
    addresses,
):
    """
    Amount used in outputs equal to the amount held by inputs,
    but rejected because one of the outputs is a floating point.
    """
    seq_no = get_seq_no(initial_mint)
    [seller_address, user1_address] = addresses

    inputs = [{"address": seller_address, "seqNo": seq_no}]
    outputs = [
        {"address": user1_address, "amount": 5.5},
        {"address": seller_address, "amount": 94.5}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)


def test_seller_xfer_negative_amount(
    helpers,
    initial_mint,
    addresses
):
    """
    Amount used in outputs equal to the amount held by inputs,
    but rejected because one of the outputs is negative.
    """
    seq_no = get_seq_no(initial_mint)
    [seller_address, user1_address] = addresses

    inputs = [{"address": seller_address, "seqNo": seq_no}]
    outputs = [
        {"address": user1_address, "amount": -10},
        {"address": seller_address, "amount": 110}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)


def test_seller_xfer_sum_of_outputs_greater_than_inputs(
    helpers,
    initial_mint,
    addresses
):
    """
    Amount used in outputs greater than the amount held by inputs,
    hence it will be rejected
    """
    seq_no = get_seq_no(initial_mint)
    [seller_address, user1_address] = addresses

    inputs = [{"address": seller_address, "seqNo": seq_no}]
    outputs = [
        {"address": user1_address, "amount": 10},
        {"address": seller_address, "amount": 100}
    ]

    with pytest.raises(RequestRejectedException):
        helpers.general.do_transfer(inputs, outputs)


def test_seller_xfer_sum_of_outputs_less_than_inputs(
    helpers,
    initial_mint,
    addresses
):
    """
    Amount used in outputs lesser than the amount held by inputs,
    hence it will be rejected
    """
    seq_no = get_seq_no(initial_mint)
    [seller_address, user1_address] = addresses

    inputs = [{"address": seller_address, "seqNo": seq_no}]
    outputs = [
        {"address": user1_address, "amount": 1},
        {"address": seller_address, "amount": 2}
    ]

    with pytest.raises(RequestRejectedException):
        helpers.general.do_transfer(inputs, outputs)


def test_seller_xfer_invalid_inputs(
    helpers,
    initial_mint,
    addresses
):
    """
    Address+seq_no repeats in the inputs of transaction, hence it will be rejected
    """
    seq_no = get_seq_no(initial_mint)
    [seller_address, user1_address] = addresses

    inputs = [
        {"address": seller_address, "seqNo": seq_no},
        {"address": seller_address, "seqNo": seq_no}
    ]
    outputs = [
        {"address": user1_address, "amount": 10},
        {"address": seller_address, "amount": 90}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_transfer(inputs, outputs)


def test_invalid_address(helpers, addresses, initial_mint):
    """
    Transfer with invalid address.
    """

    def _update_char(s, index, func):
        return s[:index] + func(s[index]) + s[index + 1:]

    def _test_invalid_address(address):
        inputs = [{ADDRESS: addresses[0], SEQNO: get_seq_no(initial_mint)}]
        outputs = [{ADDRESS: address, AMOUNT: 100}]

        with pytest.raises(RequestNackedException):
            helpers.general.do_mint(outputs)

    valid_address = addresses[1]
    invalid_address_length = b58encode_check(randomString(33).encode()).decode()
    invalid_address_character = _update_char(valid_address, 2, lambda _: '!')
    invalid_address_checksum = _update_char(
        valid_address,
        2,
        lambda c: 'B' if c == 'A' else 'A'
    )

    _test_invalid_address(invalid_address_length)
    _test_invalid_address(invalid_address_character)
    _test_invalid_address(invalid_address_checksum)


def test_seller_xfer_double_spend_attempt(looper, sdk_pool_handle,  # noqa
    nodeSetWithIntegratedTokenPlugin, public_minting, sdk_wallet_client,
    seller_address, seller_token_wallet, user1_address, user2_address):
    """
    An address tries to send to send to transactions using the same UTXO,
    one of the txn gets rejected even though the amount held by the UTXO is
    greater than the sum of outputs in both txns, since one UTXO can be used
    only once
    """

    # =============
    # Declaration of helper functions.
    # =============

    def succeeded(req_resp):
        try:
            sdk_check_reply(req_resp)
            return True
        except Exception:
            return False

    def check_output_val(address, amount):
        return check_output_val_on_all_nodes(
            nodeSetWithIntegratedTokenPlugin,
            address,
            amount
        )

    def check_no_output_val(address, amount):
        with pytest.raises(AssertionError):
            check_output_val(address, amount)

    def get_seq_no_first_utxo(address):
        get_utxo_resp = send_get_utxo(
            looper,
            address,
            sdk_wallet_client,
            sdk_pool_handle
        )

        return get_utxo_resp[OUTPUTS][0]["seqNo"]

    # =============
    # Form the two xfer requests. Each request will try to spend the same UTXO.
    # =============

    user1_gets = 3
    user2_gets = 5
    seq_no = get_seq_no_first_utxo(seller_address)
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    outputs1 = [
        {"address": user1_address, "amount": user1_gets},
        {"address": seller_address, "amount": seller_gets - user1_gets}
    ]
    outputs2 = [
        {"address": user2_address, "amount": user2_gets},
        {"address": seller_address, "amount": seller_gets - user2_gets}
    ]
    r1 = xfer_request(inputs, outputs1)
    r2 = xfer_request(inputs, outputs2)
    requests = [json.dumps(r.as_dict) for r in [r1, r2]]

    # =============
    # Send the two requests and wait for replies. Only one request
    # should succeed.
    # =============

    req_resp = sdk_send_signed_requests(sdk_pool_handle, requests)
    req_resp = sdk_get_replies(looper, req_resp)

    success1 = succeeded(req_resp[0])
    success2 = succeeded(req_resp[1])

    assert lxor(success1, success2)

    # =============
    # Check that the seller, user1, and user2, have the output or not.
    # =============

    if success1:
        check_output_val(seller_address, seller_gets - user1_gets)
        check_output_val(user1_address, user1_gets)
        check_no_output_val(user2_address, 0)
    else:
        check_output_val(seller_address, seller_gets - user2_gets)
        check_output_val(user2_address, user2_gets)
        check_no_output_val(user1_address, 0)


def test_xfer_with_multiple_inputs(helpers, seller_token_wallet):
    """
    3 inputs are used to transfer tokens to a single output
    """

    # =============
    # Mint tokens to sender's address
    # =============

    amount = 50
    first_address = helpers.wallet.add_new_addresses(seller_token_wallet, 1)[0]
    outputs = [{"address": first_address, "amount": amount}]
    mint_result = helpers.general.do_mint(outputs)
    seq_no = get_seq_no(mint_result)

    # =============
    # Transfer tokens to 3 different addresses
    # =============

    # Add 3 new addresses
    new_addresses = helpers.wallet.add_new_addresses(seller_token_wallet, 3)

    # Distribute an existing UTXO among 3 address
    inputs = [{"address": first_address, "seqNo": seq_no}]
    outputs = [{"address": address, "amount": amount // 3} for address in new_addresses]
    outputs[-1]["amount"] += amount % 3
    xfer_result = helpers.general.do_transfer(inputs, outputs)

    # =============
    # Assert tokens are in new addresses
    # =============

    xfer_seq_no = get_seq_no(xfer_result)
    new_address_utxos = helpers.general.get_utxo_addresses(new_addresses)

    assert new_address_utxos[0] == [{"address": new_addresses[0], "seqNo": xfer_seq_no, "amount": 16}]
    assert new_address_utxos[1] == [{"address": new_addresses[1], "seqNo": xfer_seq_no, "amount": 16}]
    assert new_address_utxos[2] == [{"address": new_addresses[2], "seqNo": xfer_seq_no, "amount": 18}]

    # =============
    # Transfer tokens from 3 addresses back to a single address
    # =============

    inputs = [{"address": address, "seqNo": xfer_seq_no} for address in new_addresses]
    outputs = [{"address": first_address, "amount": amount}]
    xfer_result = helpers.general.do_transfer(inputs, outputs)

    [
        first_address_utxos,
        new_address1_utxos,
        new_address2_utxos,
        new_address3_utxos,
    ] = helpers.general.get_utxo_addresses([first_address] + new_addresses)

    assert first_address_utxos == [{"address": first_address, "seqNo": xfer_seq_no + 1, "amount": amount}]
    assert new_address1_utxos == []
    assert new_address2_utxos == []
    assert new_address3_utxos == []


def test_xfer_breakdown_and_consolidate(helpers, addresses):
    """
    Breakdown utxo into separate utxos with different sequence numbers and then
    combine them.
    """
    amount = 10
    [address1, address2] = addresses
    # Mint an extra token, so all xfer requests can have a change value.
    outputs = [{ADDRESS: address1, AMOUNT: amount + 1}]

    mint_result = helpers.general.do_mint(outputs)
    seq_no = get_seq_no(mint_result)
    xfer_seq_no = seq_no + 1

    for change in range(0, amount):
        inputs = [{ADDRESS: address1, SEQNO: seq_no}]
        outputs = [
            {ADDRESS: address2, AMOUNT: 1},
            {ADDRESS: address1, AMOUNT: amount - change}
        ]
        result = helpers.general.do_transfer(inputs, outputs)
        seq_no = get_seq_no(result)

    utxos = helpers.general.get_utxo_addresses([address2])[0]

    expected_utxos = [
        {ADDRESS: address2, SEQNO: seq_no, AMOUNT: 1}
        for seq_no in range(xfer_seq_no, xfer_seq_no + amount)
    ]

    assert utxos == expected_utxos

    outputs = [{ADDRESS: address2, AMOUNT: amount}]

    result = helpers.general.do_transfer(expected_utxos, outputs)

    utxos = helpers.general.get_utxo_addresses([address2])[0]

    assert utxos == [
        {ADDRESS: address2, SEQNO: get_seq_no(result), AMOUNT: amount}
    ]
