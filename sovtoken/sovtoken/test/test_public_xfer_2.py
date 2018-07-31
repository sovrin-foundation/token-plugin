import pytest
import json

from plenum.common.exceptions import RequestNackedException, \
    RequestRejectedException
from plenum.common.txn_util import get_seq_no
from plenum.common.util import lxor
from sovtoken.constants import OUTPUTS
from sovtoken.util import update_token_wallet_with_result
from sovtoken.wallet import TokenWallet, Address
from sovtoken.test.helper import send_xfer, send_public_mint, \
    check_output_val_on_all_nodes, xfer_request, send_get_utxo
from sovtoken.test.conftest import seller_gets, total_mint
from plenum.test.helper import sdk_send_signed_requests, \
    sdk_get_replies, sdk_check_reply


@pytest.fixture(scope="module")
def user1_token_wallet():
    return TokenWallet('user1')


@pytest.fixture(scope="module")
def user2_token_wallet():
    return TokenWallet('user2')


@pytest.fixture(scope="module")
def user3_token_wallet():
    return TokenWallet('user3')


@pytest.fixture(scope="module")
def user1_address(user1_token_wallet):
    seed = 'user1000000000000000000000000000'.encode()
    user1_token_wallet.add_new_address(seed=seed)
    return next(iter(user1_token_wallet.addresses.keys()))


@pytest.fixture(scope="module")
def user2_address(user2_token_wallet):
    seed = 'user2000000000000000000000000000'.encode()
    user2_token_wallet.add_new_address(seed=seed)
    return next(iter(user2_token_wallet.addresses.keys()))


@pytest.fixture(scope="module")
def user3_address(user3_token_wallet):
    seed = 'user3000000000000000000000000000'.encode()
    user3_token_wallet.add_new_address(seed=seed)
    return next(iter(user3_token_wallet.addresses.keys()))


@pytest.fixture(scope='module')     # noqa
def valid_xfer_txn_done(public_minting, looper,
                        nodeSetWithIntegratedTokenPlugin, sdk_pool_handle,
                        seller_token_wallet, seller_address, user1_address):
    global seller_gets
    seq_no = get_seq_no(public_minting)
    user1_gets = 10
    seller_remaining = seller_gets - user1_gets
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    outputs = [[user1_address, user1_gets], [seller_address, seller_remaining]]
    res = send_xfer(looper, inputs, outputs, sdk_pool_handle)
    update_token_wallet_with_result(seller_token_wallet, res)
    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, seller_address, seller_remaining)
    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, user1_address, user1_gets)
    seller_gets = seller_remaining
    return res


def test_seller_xfer_invalid_outputs(public_minting, looper, # noqa
                                     sdk_pool_handle, seller_token_wallet,
                                     seller_address, user1_address):
    """
    Address repeats in the output of transaction, hence it will be rejected
    """
    seq_no = get_seq_no(public_minting)
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets - 10
    outputs = [[user1_address, 10], [seller_address, seller_remaining / 2],
               [seller_address, seller_remaining / 2]]
    with pytest.raises(RequestNackedException):
        send_xfer(looper, inputs, outputs, sdk_pool_handle)


def test_seller_xfer_float_amount(public_minting, looper, # noqa
                                  sdk_pool_handle, seller_token_wallet,
                                  seller_address, user1_address):
    """
    Amount used in outputs equal to the amount held by inputs,
    but rejected because one of the outputs is a floating point.
    """
    seq_no = get_seq_no(public_minting)
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets - 5.5
    outputs = [[user1_address, 5.5], [seller_address, seller_remaining]]
    with pytest.raises(RequestNackedException):
        send_xfer(looper, inputs, outputs, sdk_pool_handle)


def test_seller_xfer_negative_amount(public_minting, looper, # noqa
                                     sdk_pool_handle, seller_token_wallet,
                                     seller_address, user1_address):
    """
    Amount used in outputs equal to the amount held by inputs,
    but rejected because one of the outputs is negative.
    """
    seq_no = get_seq_no(public_minting)
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets + 10
    outputs = [[user1_address, -10], [seller_address, seller_remaining]]
    with pytest.raises(RequestNackedException):
        send_xfer(looper, inputs, outputs, sdk_pool_handle)


def test_seller_xfer_invalid_amount(public_minting, looper,     # noqa
                                    sdk_pool_handle, seller_token_wallet,
                                    seller_address, user1_address):
    """
    Amount used in outputs greater than the amount held by inputs,
    hence it will be rejected
    """
    seq_no = get_seq_no(public_minting)
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets + 10
    outputs = [[user1_address, 10], [seller_address, seller_remaining]]
    with pytest.raises(RequestRejectedException):
        send_xfer(looper, inputs, outputs, sdk_pool_handle)


def test_seller_xfer_invalid_inputs(public_minting, looper, # noqa
                                    sdk_pool_handle, seller_token_wallet,
                                    seller_address, user1_address):
    """
    Address+seq_no repeats in the inputs of transaction, hence it will be rejected
    """
    seq_no = get_seq_no(public_minting)
    inputs = [[seller_token_wallet, seller_address, seq_no],
              [seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets - 10
    outputs = [[user1_address, 10], [seller_address, seller_remaining]]
    with pytest.raises(RequestNackedException):
        send_xfer(looper, inputs, outputs, sdk_pool_handle)


def test_seller_xfer_valid(valid_xfer_txn_done):
    """
    A valid transfer txn, done successfully
    """
    pass


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

        return get_utxo_resp[OUTPUTS][0][1]

    # =============
    # Form the two xfer requests. Each request will try to spend the same UTXO.
    # =============

    user1_gets = 3
    user2_gets = 5
    seq_no = get_seq_no_first_utxo(seller_address)
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    outputs1 = [
        [user1_address, user1_gets],
        [seller_address, seller_gets - user1_gets]
    ]
    outputs2 = [
        [user2_address, user2_gets],
        [seller_address, seller_gets - user2_gets]
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



def test_query_utxo(looper, sdk_pool_handle, sdk_wallet_client, seller_token_wallet,  # noqa
                    seller_address, valid_xfer_txn_done, user1_address):
    """
    The ledger is queried for all UTXOs of a given address.
    """
    res1 = send_get_utxo(looper, seller_address, sdk_wallet_client,
                         sdk_pool_handle)
    assert res1[OUTPUTS]

    res2 = send_get_utxo(looper, user1_address, sdk_wallet_client,
                         sdk_pool_handle)

    assert res2[OUTPUTS]

    # An query for UTXOs for empty address fails
    with pytest.raises(RequestNackedException):
        send_get_utxo(looper, '', sdk_wallet_client, sdk_pool_handle)

    # An query for UTXOs for a new address returns 0 outputs
    address = Address()
    res3 = send_get_utxo(looper, address.address, sdk_wallet_client, sdk_pool_handle)
    assert len(res3[OUTPUTS]) == 0


# We can't handle multiple addresses at the moment because it requires a more
# complicated state proof. So this test has been changed to show that multiple
# addresses are not accepted.
def test_get_multiple_addresses(public_minting, looper, sdk_wallet_client, sdk_pool_handle, seller_address, SF_address):
    non_existent_address = Address().address
    addresses_to_check = [seller_address, SF_address, non_existent_address]
    with pytest.raises(RequestNackedException):
        resp = send_get_utxo(looper, addresses_to_check, sdk_wallet_client, sdk_pool_handle)
        # def address_in_outputs(address):
        #     return any(filter(lambda utxo: utxo[0] == a, resp[OUTPUTS]))

        # assert address_in_outputs(seller_address)
        # assert address_in_outputs(SF_address)
        # assert not address_in_outputs(non_existent_address)


def test_xfer_with_multiple_inputs(looper,  # noqa
                                   sdk_pool_handle,
                                   sdk_wallet_client,
                                   seller_token_wallet,
                                   trustee_wallets):
    """
    3 inputs are used to transfer tokens to a single output
    """

    # =============
    # Declaration of helper functions.
    # =============

    def create_addresses_wallet(wallet, num):
        addresses = []
        for _ in range(num):
            address = Address()
            wallet.add_new_address(address=address)
            addresses.append(address.address)

        return addresses

    def update_wallet_utxos(wallet, address):
        res = send_get_utxo(looper, address, sdk_wallet_client, sdk_pool_handle)
        update_token_wallet_with_result(seller_token_wallet, res)

    def xfer_tokens(wallet, inputs, outputs):
        inputs = [
            [wallet, address, seq_no]
            for [address, seq_no] in inputs
        ]
        res = send_xfer(looper, inputs, outputs, sdk_pool_handle)
        update_token_wallet_with_result(wallet, res)

    def addresses_utxos(wallet, address):
        return wallet.addresses[address].all_utxos

    def mint_tokens(outputs):
        send_public_mint(looper, trustee_wallets, outputs, sdk_pool_handle)

    # =============
    # Mint tokens to sender's address
    # =============

    first_address = create_addresses_wallet(seller_token_wallet, 1)[0]
    outputs = [[first_address, 50]]
    mint_tokens(outputs)
    update_wallet_utxos(seller_token_wallet, first_address)
    (seq_no, amount) = addresses_utxos(seller_token_wallet, first_address)[0]

    # =============
    # Transfer tokens to 3 different addresses
    # =============

    # Add 3 new addresses
    new_addresses = create_addresses_wallet(seller_token_wallet, 3)

    # Distribute an existing UTXO among 3 address
    inputs = [[first_address, seq_no]]
    outputs = [[address, amount // 3] for address in new_addresses]
    outputs[-1][1] += amount % 3
    xfer_tokens(seller_token_wallet, inputs, outputs)

    # =============
    # Assert tokens are in new addresses
    # =============

    assert 16 == addresses_utxos(seller_token_wallet, new_addresses[0])[0][1]
    assert 16 == addresses_utxos(seller_token_wallet, new_addresses[1])[0][1]
    assert 18 == addresses_utxos(seller_token_wallet, new_addresses[2])[0][1]

    # =============
    # Transfer tokens from 3 addresses back to a single address
    # =============

    inputs = [[address, seq_no + 1] for address in new_addresses]
    outputs = [[first_address, amount]]
    xfer_tokens(seller_token_wallet, inputs, outputs)

    assert seller_token_wallet.get_total_address_amount(first_address) == amount

