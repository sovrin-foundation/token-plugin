import pytest

from plenum.common.constants import NYM
from plenum.server.plugin.fees.src.wallet import FeeSupportedWallet
from plenum.server.plugin.token.src.constants import XFER_PUBLIC
from plenum.server.plugin.token.src.main import integrate_plugin_in_node as enable_token
from plenum.server.plugin.fees.src.main import integrate_plugin_in_node as enable_fees
from plenum.server.plugin.token.src.util import register_token_wallet_with_client
from plenum.server.plugin.token.test.helper import send_get_utxo, send_xfer

# fixtures, do not remove
from plenum.test.conftest import *
from plenum.server.plugin.token.test.conftest import trustee_wallets, SF_address, \
    seller_address, seller_token_wallet, SF_token_wallet, public_minting, \
    tokens_distributed
from plenum.server.plugin.token.test.test_public_xfer_1 import user1_address, \
    user1_token_wallet, user2_address, user2_token_wallet, user3_address, \
    user3_token_wallet


@pytest.fixture(scope="module")
def do_post_node_creation():
    # Integrate plugin into each node.
    def _post_node_creation(node):
        enable_token(node)
        enable_fees(node)

    return _post_node_creation


@pytest.fixture(scope="module")
def nodeSetWithIntegratedTokenPlugin(do_post_node_creation, tconf, txnPoolNodeSet):
    return txnPoolNodeSet


@pytest.fixture(scope="module")
def fees(request):
    default_fees = {
        NYM: 4,
        XFER_PUBLIC: 8
    }
    fees = getValueFromModule(request, "TXN_FEES", default_fees)
    return fees


# Wallet should have support to track fees

@pytest.fixture(scope="module")
def seller_token_wallet():
    return FeeSupportedWallet('SELLER')


@pytest.fixture(scope="module") # noqa
def user1_token_wallet():
    return FeeSupportedWallet('user1')


@pytest.fixture(scope="module") # noqa
def user2_token_wallet():
    return FeeSupportedWallet('user2')


@pytest.fixture(scope="module") # noqa
def user3_token_wallet():
    return FeeSupportedWallet('user3')
