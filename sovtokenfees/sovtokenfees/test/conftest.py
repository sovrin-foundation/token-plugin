import pytest

from plenum import PLUGIN_CLIENT_REQUEST_FIELDS
from plenum.common.txn_util import get_seq_no, get_payload_data
from plenum.common.constants import NYM
from plenum.test.helper import sdk_get_and_check_replies

# fixtures, do not remove
from indy_node.test.conftest import *
from indy_common.constants import NYM

from sovtoken.constants import (
    XFER_PUBLIC, RESULT, ADDRESS, AMOUNT, SEQNO
)
from sovtoken.main import integrate_plugin_in_node as enable_token
from sovtoken.test.conftest import trustee_wallets, steward_wallets, \
    increased_trustees
from sovtoken.test.helper import user1_token_wallet


from sovtokenfees.main import integrate_plugin_in_node as enable_fees
from sovtokenfees import CLIENT_REQUEST_FIELDS
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import (
    get_amount_from_token_txn, nyms_with_fees,
    send_and_check_nym_with_fees, send_and_check_transfer
)
from sovtokenfees.test.helpers import form_helpers


# TODO ST-525 reorder imports

@pytest.fixture(scope="module")
def do_post_node_creation():
    # Integrate plugin into each node.
    PLUGIN_CLIENT_REQUEST_FIELDS.update(CLIENT_REQUEST_FIELDS)

    def _post_node_creation(node):
        enable_token(node)
        enable_fees(node)

    return _post_node_creation


@pytest.fixture(scope="module")
def nodeSetWithIntegratedTokenPlugin(do_post_node_creation, tconf, nodeSet):
    return nodeSet


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
def address_main(helpers):
    return helpers.wallet.create_address()


@pytest.fixture()
def mint_tokens(helpers, address_main):
    return helpers.general.do_mint([
        {ADDRESS: address_main, AMOUNT: 1000},
    ])


def pytest_addoption(parser):
    parser.addoption(
        "--test_helpers",
        action="store_true",
        dest="test_helpers",
        default=False,
        help="run helper tests"
    )


def pytest_configure(config):
    if not config.option.test_helpers:
        setattr(config.option, 'markexpr', 'not helper_test')


@pytest.fixture()
def xfer_addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def xfer_mint_tokens(helpers, xfer_addresses):
    outputs = [{ADDRESS: xfer_addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


@pytest.fixture
def curr_seq_no(xfer_mint_tokens):
    return get_seq_no(xfer_mint_tokens)


@pytest.fixture
def curr_amount(xfer_mint_tokens):
    return get_amount_from_token_txn(xfer_mint_tokens)


@pytest.fixture
def curr_utxo(curr_seq_no, curr_amount):
    return {
        'amount': curr_amount,
        'seq_no': curr_seq_no
    }


@pytest.fixture
def send_and_check_nym_with_fees_curr_utxo(looper, helpers, fees_set, xfer_addresses, curr_utxo):

    def wrapped(addresses=None, check_reply=True, nym_with_fees=None):
        addresses = xfer_addresses if addresses is None else addresses

        curr_utxo['amount'], curr_utxo['seq_no'], resp = send_and_check_nym_with_fees(
            helpers, fees_set, curr_utxo['seq_no'],
            looper, addresses, curr_utxo['amount'],
            check_reply=check_reply, nym_with_fees=nym_with_fees
        )

        return curr_utxo, resp

    return wrapped


@pytest.fixture
def send_and_check_transfer_curr_utxo(looper, helpers, fees, xfer_addresses, curr_utxo):

    def wrapped(addresses=None, check_reply=True, transfer_summ=20):
        addresses = xfer_addresses if addresses is None else addresses

        curr_utxo['amount'], curr_utxo['seq_no'], resp = send_and_check_transfer(
            helpers, addresses, fees, looper,
            curr_utxo['amount'], curr_utxo['seq_no'],
            check_reply=check_reply, transfer_summ=transfer_summ
        )

        return curr_utxo, resp

    return wrapped
