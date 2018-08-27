from sovtoken.constants import XFER_PUBLIC, RESULT
from sovtoken.main import integrate_plugin_in_node as enable_token
from sovtokenfees.main import integrate_plugin_in_node as enable_fees

from plenum.common.util import randomString
from plenum.common.constants import TARGET_NYM, TRUSTEE_STRING, VERKEY

# fixtures, do not remove
from plenum.test.conftest import *
from plenum import PLUGIN_CLIENT_REQUEST_FIELDS
from sovtokenfees import CLIENT_REQUEST_FIELDS

from sovtoken.test.conftest import trustee_wallets, steward_wallets
from sovtoken.test.helper import user1_token_wallet
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


@pytest.fixture()
def fees_set(helpers, fees):
    result = helpers.general.do_set_fees(fees)
    return get_payload_data(result)


@pytest.fixture(scope="module")
def helpers(
    nodeSetWithIntegratedTokenPlugin,
    looper,
    sdk_pool_handle,
    trustee_wallets,
    steward_wallets,
    sdk_wallet_client,
    sdk_wallet_steward
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


@pytest.fixture(autouse=True)
def reset_fees(helpers):
    helpers.node.reset_fees()


@pytest.fixture()
def increased_trustees(helpers, trustee_wallets, sdk_wallet_trustee):
    seeds = [randomString(32) for _ in range(3)]

    requests = [
        helpers.request.nym(seed=seed, role=TRUSTEE_STRING)
        for seed in seeds
    ]

    responses = helpers.sdk.send_and_check_request_objects(requests)

    wallets = [helpers.wallet.create_client_wallet(seed) for seed in seeds]

    yield trustee_wallets + wallets

    # TODO: Not certain if this is actually changing the role.
    def _update_nym_standard_user(response):
        data = get_payload_data(response[RESULT])
        request = helpers.request.nym(
            dest=data[TARGET_NYM],
            verkey=data[VERKEY],
            role=None
        )
        return request

    requests = [
        _update_nym_standard_user(response)
        for _, response in responses
    ]

    helpers.sdk.send_and_check_request_objects(requests)
