import pytest
import json

from ledger.util import F
from plenum.common.exceptions import RequestNackedException, \
    RequestRejectedException
from plenum.common.util import lxor
from plenum.server.plugin.token.src.constants import OUTPUTS
from plenum.server.plugin.token.src.util import update_token_wallet_with_result
from plenum.server.plugin.token.src.wallet import TokenWallet, Address
from plenum.server.plugin.token.test.helper import send_xfer, \
    check_output_val_on_all_nodes, xfer_request, send_get_utxo
from plenum.server.plugin.token.test.conftest import seller_gets, total_mint
from plenum.test.helper import sdk_send_signed_requests, \
    sdk_get_and_check_replies


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
    seq_no = public_minting[F.seqNo.name]
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
    seq_no = public_minting[F.seqNo.name]
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
    seq_no = public_minting[F.seqNo.name]
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
    seq_no = public_minting[F.seqNo.name]
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
    seq_no = public_minting[F.seqNo.name]
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
    seq_no = public_minting[F.seqNo.name]
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
                                          nodeSetWithIntegratedTokenPlugin,
                                          seller_token_wallet, seller_address,
                                          valid_xfer_txn_done, user1_address,
                                          user2_address):
    """
    An address tries to send to send to transactions using the same UTXO,
    one of the txn gets rejected even though the amount held by the UTXO is
    greater than the sum of outputs in both txns, since one UTXO can be used
    only once
    """
    seq_no = valid_xfer_txn_done[F.seqNo.name]
    user1_gets = 3
    user2_gets = 5
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets - user1_gets
    outputs1 = [[user1_address, user1_gets], [seller_address, seller_remaining]]
    seller_remaining -= user2_gets
    outputs2 = [[user2_address, user2_gets], [seller_address, seller_remaining]]
    r1 = xfer_request(inputs, outputs1)
    r1 = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(r1.as_dict), ])
    r2 = xfer_request(inputs, outputs2)
    r2 = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(r2.as_dict), ])
    # So that both requests are sent simultaneously
    looper.runFor(.2)

    # Both requests should not be successful, one and only one should be
    success1, success2 = False, False
    try:
        check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin,
                                      user1_address, user1_gets)
        success1 = True
    except Exception:
        pass

    try:
        check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, user2_address, user2_gets)
        success2 = True
    except Exception:
        pass

    assert lxor(success1, success2)

    request = r1 if success1 else r2
    _, rep = sdk_get_and_check_replies(looper, request)[0]
    update_token_wallet_with_result(seller_token_wallet, rep['result'])

    if success1:
        check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, seller_address,
                                      seller_gets - user1_gets)
    else:
        check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, seller_address,
                                      seller_gets - user2_gets)


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


# def test_get_multiple_addresses(public_minting, looper, sdk_wallet_client, sdk_pool_handle, seller_address, SF_address):
#     non_existent_address = Address().address
#     addresses_to_check = [seller_address, SF_address, non_existent_address]
#     resp = send_get_utxo(looper, addresses_to_check, sdk_wallet_client, sdk_pool_handle)
#     address_in_outputs = lambda a: any(filter(lambda utxo: utxo[0] == a, resp[OUTPUTS]))
#     assert address_in_outputs(seller_address)
#     assert address_in_outputs(SF_address)
#     assert not address_in_outputs(non_existent_address)


def test_xfer_with_multiple_inputs(public_minting, looper,  # noqa
                                   sdk_pool_handle, sdk_wallet_client,
                                   seller_token_wallet, seller_address,
                                   user1_address):
    """
    3 inputs are used to transfer tokens to a single output
    """
    send_get_utxo(looper, seller_address, sdk_wallet_client, sdk_pool_handle)
    utxos = [_ for lst in seller_token_wallet.get_all_wallet_utxos().values()
             for _ in lst]
    assert utxos
    old_count = len(utxos)
    # Add 3 new addresses
    new_addrs = []
    for i in range(3):
        new_addrs.append(Address())
        seller_token_wallet.add_new_address(address=new_addrs[-1])
    seq_no, amount = utxos[0]
    # Distribute an existing UTXO among 3 address
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    outputs = [[addr.address, amount // 3] for addr in new_addrs]
    outputs[-1][1] += amount % 3
    res = send_xfer(looper, inputs, outputs, sdk_pool_handle)
    update_token_wallet_with_result(seller_token_wallet, res)

    new_utxos = [_ for lst in seller_token_wallet.get_all_wallet_utxos().values()
                 for _ in lst]
    # Since 1 existing UTXO is spent and 3 new created
    assert len(new_utxos) - old_count == 2

    new_seq_no = new_utxos[0][0]
    sum_utxo_val = sum(t[1] for t in new_utxos)
    seller_gets = sum_utxo_val - sum_utxo_val
    inputs = [[seller_token_wallet, addr.address, new_seq_no]
              for addr in new_addrs]
    outputs = [[user1_address, sum_utxo_val], ]
    res = send_xfer(looper, inputs, outputs, sdk_pool_handle)
    update_token_wallet_with_result(seller_token_wallet, res)
    assert seller_token_wallet.get_total_wallet_amount() == seller_gets

