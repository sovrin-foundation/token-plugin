import pytest

from ledger.util import F
from plenum.client.wallet import Wallet
from plenum.common.constants import STEWARD
from plenum.common.txn_util import get_seq_no
from sovtoken.main import integrate_plugin_in_node
from sovtoken.util import \
    register_token_wallet_with_client, update_token_wallet_with_result
from sovtoken.test.wallet import TokenWallet
from plenum.test.conftest import *
from sovtoken.test.helper import send_get_utxo, send_xfer, \
    do_public_minting
from sovtoken.test.helpers import form_helpers

total_mint = 100
seller_gets = 40


# def build_wallets_from_data(name_seeds, looper, pool_name):
def build_wallets_from_data(name_seeds):
    wallets = []
    for name, seed in name_seeds:
        # wallet_handle = looper.loop.run_until_complete(
        #     _gen_wallet_handler(pool_name, name))
        # looper.loop.run_until_complete(
        #     create_and_store_my_did(wallet_handle,
        #                             json.dumps({'seed': seed})))
        # wallets.append(wallet_handle)
        w = Wallet(name)
        w.addIdentifier(seed=seed.encode())
        wallets.append(w)
    return wallets


@pytest.fixture(scope="module")
def SF_token_wallet():
    return TokenWallet('SF_MASTER')


@pytest.fixture(scope="module")
def SF_address(SF_token_wallet):
    seed = 'sf000000000000000000000000000000'.encode()
    SF_token_wallet.add_new_address(seed=seed)
    return next(iter(SF_token_wallet.addresses.keys()))


@pytest.fixture(scope="module")
def seller_token_wallet():
    return TokenWallet('SELLER')


@pytest.fixture(scope="module")
def seller_address(seller_token_wallet):
    # Token selling/buying platform's address
    seed = 'se000000000000000000000000000000'.encode()
    seller_token_wallet.add_new_address(seed=seed)
    return next(iter(seller_token_wallet.addresses.keys()))


@pytest.fixture(scope="module")
def trustee_wallets(trustee_data, looper, sdk_pool_data):
    return build_wallets_from_data(trustee_data)


@pytest.fixture(scope="module")
def steward_wallets(poolTxnData):
    steward_data = get_data_for_role(poolTxnData, STEWARD)
    return build_wallets_from_data(steward_data)


@pytest.fixture(scope="module")
def do_post_node_creation():
    # Integrate plugin into each node.
    def _post_node_creation(node):
        integrate_plugin_in_node(node)

    return _post_node_creation


@pytest.fixture(scope="module")
def nodeSetWithIntegratedTokenPlugin(do_post_node_creation, tconf, txnPoolNodeSet):
    return txnPoolNodeSet


@pytest.fixture(scope='module') # noqa
def public_minting(nodeSetWithIntegratedTokenPlugin, looper, sdk_pool_handle,
                   trustee_wallets, SF_address, seller_address):
    return do_public_minting(looper, trustee_wallets, sdk_pool_handle, total_mint,
                             total_mint - seller_gets, SF_address,
                             seller_address)


@pytest.fixture(scope="module")
def tokens_distributed(public_minting, seller_token_wallet, seller_address,
                       user1_address, user1_token_wallet,
                       user2_address, user2_token_wallet,
                       user3_address, user3_token_wallet, looper, sdk_pool_handle,
                       sdk_wallet_client):
    # register_token_wallet_with_client(client1, seller_token_wallet)
    res = send_get_utxo(looper, seller_address, sdk_wallet_client, sdk_pool_handle)
    update_token_wallet_with_result(seller_token_wallet, res)
    total_amount = seller_token_wallet.get_total_address_amount(seller_address)

    inputs = [[seller_token_wallet, seller_address, seq_no] for seq_no, _ in
              next(iter(seller_token_wallet.get_all_address_utxos(seller_address).values()))]
    each_user_share = total_amount // 3
    outputs = [[user1_address, each_user_share],
               [user2_address, each_user_share],
               [user3_address, each_user_share],
               [seller_address, total_amount % 3]]
    res = send_xfer(looper, inputs, outputs, sdk_pool_handle)
    update_token_wallet_with_result(seller_token_wallet, res)
    seq_no = get_seq_no(res)
    for w, a in [(user1_token_wallet, user1_address),
                 (user2_token_wallet, user2_address),
                 (user3_token_wallet, user3_address)]:
        res = send_get_utxo(looper, a, sdk_wallet_client, sdk_pool_handle)
        update_token_wallet_with_result(w, res)
    return seq_no


@pytest.fixture(scope='module')
def helpers(
    nodeSetWithIntegratedTokenPlugin,
    looper,
    sdk_pool_handle,
    trustee_wallets,
    steward_wallets,
    sdk_wallet_client,
    sdk_wallet_steward,
):
    return form_helpers(
        nodeSetWithIntegratedTokenPlugin,
        looper,
        sdk_pool_handle,
        trustee_wallets,
        steward_wallets,
        sdk_wallet_client,
        sdk_wallet_steward
    )
