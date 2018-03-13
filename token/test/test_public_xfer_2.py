import pytest

from ledger.util import F
from plenum.common.util import lxor
from plugin.token.src.constants import OUTPUTS
from plugin.token.src.util import register_token_wallet_with_client
from plugin.token.src.wallet import TokenWallet, Address
from plugin.token.test.helper import do_public_minting, send_xfer, \
    check_output_val_on_all_nodes, xfer_request, send_get_utxo
from plenum.test.pool_transactions.conftest import clientAndWallet1, \
    client1, wallet1, client1Connected, looper

total_mint = 100
seller_gets = 40


@pytest.fixture(scope='module') # noqa
def public_minting(looper, txnPoolNodeSet, client1, # noqa
                   wallet1, client1Connected, trustee_wallets,
                   SF_address, seller_address):
    return do_public_minting(looper, trustee_wallets, client1, total_mint,
                             total_mint - seller_gets, SF_address,
                             seller_address)


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


def test_seller_xfer_invalid_outputs(public_minting, looper, txnPoolNodeSet,# noqa
                                     client1, seller_token_wallet,
                                     seller_address, user1_address):
    """
    Address repeats in the output of transaction, hence it will be rejected
    """
    global seller_gets
    seq_no = public_minting[F.seqNo.name]
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets - 10
    outputs = [[user1_address, 10], [seller_address, seller_remaining / 2],
               [seller_address, seller_remaining / 2]]
    with pytest.raises(AssertionError):
        send_xfer(looper, inputs, outputs, client1)


def test_seller_xfer_float_amount(public_minting, looper, txnPoolNodeSet, # noqa
                                    client1, seller_token_wallet,
                                    seller_address, user1_address):
    """
    Amount used in outputs equal to the amount held by inputs,
    but rejected because one of the outputs is a floating point.
    """
    global seller_gets
    seq_no = public_minting[F.seqNo.name]
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets - 5.5
    outputs = [[user1_address, 5.5], [seller_address, seller_remaining]]
    with pytest.raises(AssertionError):
        send_xfer(looper, inputs, outputs, client1)


def test_seller_xfer_negative_amount(public_minting, looper, txnPoolNodeSet, # noqa
                                    client1, seller_token_wallet,
                                    seller_address, user1_address):
    """
    Amount used in outputs equal to the amount held by inputs,
    but rejected because one of the outputs is negative.
    """
    global seller_gets
    seq_no = public_minting[F.seqNo.name]
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets + 10
    outputs = [[user1_address, -10], [seller_address, seller_remaining]]
    with pytest.raises(AssertionError):
        send_xfer(looper, inputs, outputs, client1)


def test_seller_xfer_invalid_amount(public_minting, looper, txnPoolNodeSet, # noqa
                                    client1, seller_token_wallet,
                                    seller_address, user1_address):
    """
    Amount used in outputs greater than the amount held by inputs,
    hence it will be rejected
    """
    global seller_gets
    seq_no = public_minting[F.seqNo.name]
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets + 10
    outputs = [[user1_address, 10], [seller_address, seller_remaining]]
    with pytest.raises(AssertionError):
        send_xfer(looper, inputs, outputs, client1)


def test_seller_xfer_invalid_inputs(public_minting, looper, txnPoolNodeSet, # noqa
                                    client1, seller_token_wallet,
                                    seller_address, user1_address):
    """
    Address+seq_no repeats in the inputs of transaction, hence it will be rejected
    """
    global seller_gets
    seq_no = public_minting[F.seqNo.name]
    inputs = [[seller_token_wallet, seller_address, seq_no],
              [seller_token_wallet, seller_address, seq_no]]
    seller_remaining = seller_gets - 10
    outputs = [[user1_address, 10], [seller_address, seller_remaining]]
    with pytest.raises(AssertionError):
        send_xfer(looper, inputs, outputs, client1)


@pytest.fixture(scope='module')     # noqa
def valid_xfer_txn_done(public_minting, looper, txnPoolNodeSet, client1,
                        seller_token_wallet, seller_address, user1_address):
    global seller_gets
    seq_no = public_minting[F.seqNo.name]
    user1_gets = 10
    seller_gets -= user1_gets
    inputs = [[seller_token_wallet, seller_address, seq_no]]
    outputs = [[user1_address, user1_gets], [seller_address, seller_gets]]
    req = send_xfer(looper, inputs, outputs, client1)
    check_output_val_on_all_nodes(txnPoolNodeSet, seller_address, seller_gets)
    check_output_val_on_all_nodes(txnPoolNodeSet, user1_address, user1_gets)
    result, _ = client1.getReply(req.identifier, req.reqId)
    return result


def test_seller_xfer_valid(valid_xfer_txn_done):
    """
    A valid transfer txn, done successfully
    """
    pass


def test_seller_xfer_double_spend_attempt(looper, txnPoolNodeSet, client1,  # noqa
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
    client1.submitReqs(r1)
    r2 = xfer_request(inputs, outputs2)
    client1.submitReqs(r2)
    # So that both requests are sent simultaneously
    looper.runFor(.2)

    # Both requests should not be successful, one and only one should be
    sucess1, sucess2 = False, False
    try:
        check_output_val_on_all_nodes(txnPoolNodeSet, user1_address, user1_gets)
        sucess1 = True
    except Exception:
        pass

    try:
        check_output_val_on_all_nodes(txnPoolNodeSet, user2_address, user2_gets)
        sucess2 = True
    except Exception:
        pass

    assert lxor(sucess1, sucess2)

    if sucess1:
        check_output_val_on_all_nodes(txnPoolNodeSet, seller_address,
                                      seller_gets - user1_gets)
    else:
        check_output_val_on_all_nodes(txnPoolNodeSet, seller_address,
                                      seller_gets - user2_gets)


def test_query_utxo(looper, txnPoolNodeSet, client1, wallet1, seller_token_wallet,  # noqa
                    seller_address, valid_xfer_txn_done, user1_address):
    """
    The ledger is queried for all UTXOs of a given address.
    """
    req1 = send_get_utxo(looper, seller_address, wallet1, client1)
    rep1, _ = client1.getReply(wallet1.defaultId, req1.reqId)
    assert rep1[OUTPUTS]

    req2 = send_get_utxo(looper, user1_address, wallet1, client1)
    rep2, _ = client1.getReply(wallet1.defaultId, req2.reqId)
    assert rep2[OUTPUTS]

    # An query for UTXOs for empty address fails
    with pytest.raises(AssertionError):
        send_get_utxo(looper, '', wallet1, client1)

    # An query for UTXOs for a new address returns 0 outputs
    address = Address()
    req3 = send_get_utxo(looper, address.address, wallet1, client1)
    rep3, _ = client1.getReply(wallet1.defaultId, req3.reqId)
    assert len(rep3[OUTPUTS]) == 0


def test_xfer_with_multiple_inputs(public_minting, looper, txnPoolNodeSet,  # noqa
                                   client1, wallet1, seller_token_wallet,
                                   seller_address, user1_address):
    """
    3 inputs are used to transfer tokens to a single output
    """
    register_token_wallet_with_client(client1, seller_token_wallet)
    send_get_utxo(looper, seller_address, wallet1, client1)
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
    send_xfer(looper, inputs, outputs, client1)

    new_utxos = [_ for lst in seller_token_wallet.get_all_wallet_utxos().values()
                 for _ in lst]
    # Since 1 existing UTXO is spent and 2 new created
    assert len(new_utxos) - old_count == 2

    new_seq_no = new_utxos[0][0]
    sum_utxo_val = sum(t[1] for t in new_utxos)
    seller_gets = sum_utxo_val - sum_utxo_val
    inputs = [[seller_token_wallet, addr.address, new_seq_no]
              for addr in new_addrs]
    outputs = [[user1_address, sum_utxo_val], ]
    send_xfer(looper, inputs, outputs, client1)

    assert seller_token_wallet.get_total_wallet_amount() == seller_gets

