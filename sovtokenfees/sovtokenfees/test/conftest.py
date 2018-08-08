from sovtoken.constants import XFER_PUBLIC
from sovtoken.main import integrate_plugin_in_node as enable_token
from sovtokenfees.test.wallet import FeeSupportedWallet
from sovtokenfees.main import integrate_plugin_in_node as enable_fees

# fixtures, do not remove
from plenum.test.conftest import *
from plenum import PLUGIN_CLIENT_REQUEST_FIELDS
from sovtokenfees import CLIENT_REQUEST_FIELDS

from sovtoken.test.conftest import trustee_wallets, SF_address, \
    seller_address, seller_token_wallet, SF_token_wallet, public_minting, \
    tokens_distributed
from sovtoken.test.helper import user1_address, \
    user1_token_wallet, user2_address, user2_token_wallet, user3_address, \
    user3_token_wallet
from sovtokenfees.test.helper import set_fees
from sovtokenfees.test.helpers import form_helpers


@pytest.fixture(scope="module")
def do_post_node_creation():
    # Integrate plugin into each node.
    PLUGIN_CLIENT_REQUEST_FIELDS.update(CLIENT_REQUEST_FIELDS)

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


@pytest.fixture(scope="module")
def fees_set(looper, nodeSetWithIntegratedTokenPlugin, sdk_pool_handle,
             trustee_wallets, fees):
    return set_fees(looper, trustee_wallets, fees, sdk_pool_handle)


# Wallet should have support to track sovtokenfees

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


@pytest.fixture(scope="module")
def helpers(
    nodeSetWithIntegratedTokenPlugin,
    looper,
    sdk_pool_handle,
    trustee_wallets,
    sdk_wallet_client,
    sdk_wallet_steward
):
    return form_helpers(
        nodeSetWithIntegratedTokenPlugin,
        looper,
        sdk_pool_handle,
        trustee_wallets,
        sdk_wallet_client,
        sdk_wallet_steward
    )
