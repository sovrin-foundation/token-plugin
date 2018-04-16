from plenum.server.plugin.fees.src.wallet import FeeSupportedWallet
from plenum.server.plugin.token.src.constants import XFER_PUBLIC
from plenum.server.plugin.token.src.main import update_node_obj as enable_token
from plenum.server.plugin.fees.src.main import update_node_obj as enable_fees

# fixtures, do not remove
from plenum.test.conftest import *


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
