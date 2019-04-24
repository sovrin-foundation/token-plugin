import pytest
from enum import Enum, unique
from collections import defaultdict

from plenum import PLUGIN_CLIENT_REQUEST_FIELDS
from plenum.common.txn_util import get_seq_no, get_payload_data
from plenum.common.types import f
from plenum.common.constants import DATA
from plenum.test.helper import sdk_get_and_check_replies
from plenum.test.conftest import getValueFromModule

# fixtures, do not remove
from indy_node.test.conftest import *
from indy_common.constants import NYM

from sovtoken.constants import (
    XFER_PUBLIC, RESULT, ADDRESS, AMOUNT, SEQNO, OUTPUTS
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
    send_and_check_nym_with_fees, send_and_check_transfer,
    InputsStrategy, OutputsStrategy,
    prepare_inputs as prepare_inputs_h,
    prepare_outputs as prepare_outputs_h,
    send_and_check_xfer as send_and_check_xfer_h
)
from sovtokenfees.test.helpers import form_helpers


@unique
class MintStrategy(Enum):
    single_first = 1  # mint only for the first address
    multiple_equal = 2  # mint equal values for all addresses

# ######################
# configuration fixtures
# ######################


@pytest.fixture(scope="module")
def fees(request):
    default_fees = {
        NYM: 4,
        XFER_PUBLIC: 8
    }
    fees = getValueFromModule(request, "TXN_FEES", default_fees)
    return fees


@pytest.fixture
def addresses_num(request):
    return getValueFromModule(request, "ADDRESSES_NUM", 2)


@pytest.fixture
def mint_strategy(request):
    return getValueFromModule(request, "MINT_STRATEGY", MintStrategy.single_first)


@pytest.fixture
def mint_amount(request):
    return getValueFromModule(request, "MINT_AMOUNT", 1000)


@pytest.fixture
def inputs_strategy(request):
    return getValueFromModule(request, "INPUTS_STRATEGY", InputsStrategy.all_utxos)


@pytest.fixture
def outputs_strategy(request):
    return getValueFromModule(request, "OUTPUTS_STRATEGY", OutputsStrategy.transfer_equal)


# makes sense not for all outputs strategies
@pytest.fixture
def transfer_amount(request):
    return getValueFromModule(request, "TRANSFER_AMOUNT", 20)


# #########################

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


@pytest.fixture
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


@pytest.fixture
def address_main(helpers):
    return helpers.wallet.create_address()


@pytest.fixture
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


@pytest.fixture
def addresses(helpers, addresses_num):
    return helpers.wallet.create_new_addresses(addresses_num)


@pytest.fixture
def mint_amounts(request, addresses, mint_strategy, mint_amount):
    amounts = {addr: 0 for addr in addresses}

    if mint_strategy == MintStrategy.single_first:
        amounts[addresses[0]] = mint_amount
    elif mint_strategy == MintStrategy.multiple_equal:
        amounts = {addr: mint_amount for addr in addresses}
    else:
        raise ValueError("unexpected mint strategy: {}".format(mint_strategy))

    return amounts


@pytest.fixture
def mint_multiple_tokens(helpers, addresses, mint_amounts):
    outputs = [
        {ADDRESS: addr, AMOUNT: mint_amounts[addr]} for addr in addresses
        if mint_amounts[addr]
    ]
    res = helpers.general.do_mint(outputs)
    for addr in addresses:
        helpers.wallet.handle_get_utxo_response(
            helpers.general.do_get_utxo(addr))
    return res


@pytest.fixture
def io_addresses(addresses, outputs_strategy):
    return (
        (addresses[:2], addresses[2:])
        if outputs_strategy == OutputsStrategy.transfer_equal else
        (addresses[:2], addresses)
    )


@pytest.fixture
def prepare_inputs(helpers, inputs_strategy, io_addresses):
    _inputs_strategy = inputs_strategy

    def wrapped(addresses=None, inputs_strategy=None):
        addresses = io_addresses[0] if addresses is None else addresses
        inputs_strategy = (
            _inputs_strategy if inputs_strategy is None else inputs_strategy
        )

        return prepare_inputs_h(helpers, addresses, strategy=inputs_strategy)

    return wrapped


@pytest.fixture
def prepare_outputs(helpers, fees, outputs_strategy, transfer_amount, io_addresses, prepare_inputs):
    _outputs_strategy = outputs_strategy

    def wrapped(inputs=None, addresses=None, outputs_strategy=None):

        inputs = prepare_inputs() if inputs is None else inputs
        addresses = io_addresses[1] if addresses is None else addresses
        outputs_strategy = (
            _outputs_strategy if outputs_strategy is None else outputs_strategy
        )

        return prepare_outputs_h(
            helpers, fees, inputs, addresses,
            strategy=outputs_strategy, transfer_amount=transfer_amount
        )

    return wrapped


@pytest.fixture
def send_and_check_xfer(
    looper, helpers, prepare_inputs, prepare_outputs,
):
    def wrapped(inputs=None, outputs=None):
        inputs = prepare_inputs() if inputs is None else inputs
        outputs = prepare_outputs(inputs) if outputs is None else outputs
        return send_and_check_xfer_h(looper, helpers, inputs, outputs)

    return wrapped


# TODO old fixtures for backward compartibility
@pytest.fixture
def xfer_addresses(addresses):
    return addresses


@pytest.fixture
def xfer_mint_tokens(mint_multiple_tokens):
    return mint_multiple_tokens


@pytest.fixture
def curr_seq_no(mint_multiple_tokens):
    return get_seq_no(mint_multiple_tokens)


@pytest.fixture
def curr_amount(mint_multiple_tokens):
    return get_amount_from_token_txn(mint_multiple_tokens)


@pytest.fixture
def curr_utxo(curr_seq_no, curr_amount):
    return {
        'amount': curr_amount,
        'seq_no': curr_seq_no
    }


@pytest.fixture
def send_and_check_nym_with_fees_curr_utxo(looper, helpers, fees_set, addresses, curr_utxo):
    _addresses = addresses

    def wrapped(addresses=None, check_reply=True, nym_with_fees=None):
        addresses = _addresses if addresses is None else addresses

        curr_utxo['amount'], curr_utxo['seq_no'], resp = send_and_check_nym_with_fees(
            helpers, fees_set, curr_utxo['seq_no'],
            looper, addresses, curr_utxo['amount'],
            check_reply=check_reply, nym_with_fees=nym_with_fees
        )

        return curr_utxo, resp

    return wrapped


@pytest.fixture
def send_and_check_transfer_curr_utxo(looper, helpers, fees, addresses, curr_utxo):
    _addresses = addresses

    def wrapped(addresses=None, check_reply=True, transfer_summ=20):
        addresses = _addresses if addresses is None else addresses

        curr_utxo['amount'], curr_utxo['seq_no'], resp = send_and_check_transfer(
            helpers, addresses, fees, looper,
            curr_utxo['amount'], curr_utxo['seq_no'],
            check_reply=check_reply, transfer_summ=transfer_summ
        )

        return curr_utxo, resp

    return wrapped
