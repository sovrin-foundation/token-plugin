from abc import ABCMeta, abstractmethod

from sovtoken.test.conftest import build_wallets_from_data

from plenum.common.constants import NYM, STEWARD, TARGET_NYM, TRUSTEE_STRING
from sovtoken.test.helpers import libloader


import pytest
from enum import Enum, unique

from plenum import PLUGIN_CLIENT_REQUEST_FIELDS
from plenum.common.txn_util import get_seq_no, get_payload_data
from plenum.test.helper import sdk_get_and_check_replies
from plenum.test.conftest import getValueFromModule, sdk_wallet_handle
from sovtoken.test.conftest import sdk_trustees, sdk_stewards

# fixtures, do not remove
from indy_node.test.conftest import *

from sovtoken.constants import (
    XFER_PUBLIC, RESULT, ADDRESS, AMOUNT, SEQNO, OUTPUTS
)
from sovtoken.main import integrate_plugin_in_node as enable_token


from sovtokenfees.main import integrate_plugin_in_node as enable_fees
from sovtokenfees.constants import MAX_FEE_OUTPUTS
from sovtokenfees import CLIENT_REQUEST_FIELDS
from sovtokenfees.test.constants import (
    NYM_FEES_ALIAS, XFER_PUBLIC_FEES_ALIAS, txn_type_to_alias
)
from sovtokenfees.test.helper import (
    get_amount_from_token_txn,
    send_and_check_nym_with_fees, send_and_check_transfer,
    InputsStrategy, OutputsStrategy,
    prepare_inputs as prepare_inputs_h,
    prepare_outputs as prepare_outputs_h,
    send_and_check_xfer as send_and_check_xfer_h,
    send_and_check_nym as send_and_check_nym_h
)
from sovtokenfees.test.helpers import form_helpers

from plenum.test.conftest import get_data_for_role


from stp_core.common.log import Logger
Logger().enableStdLogging()


@unique
class MintStrategy(Enum):
    first_only = 1  # mint only for the first address
    all_equal = 2  # mint equal values for all addresses


class IOAddresses(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class IOAddressesDynamic(IOAddresses):
    def __init__(self, helpers, addresses):
        self._addresses = [helpers.wallet.address_map[addr] for addr in addresses]

    def __call__(self, txn_type=None):
        with_utxos = [addr.address for addr in self._addresses if addr.total_amount]
        no_utxos = [addr.address for addr in self._addresses if not addr.total_amount]
        assert with_utxos

        if txn_type == XFER_PUBLIC:
            # try to make them near equal
            border = len(self._addresses) // 2 or 1
            return (with_utxos[:border], with_utxos[border:] + no_utxos)
        else:
            return (with_utxos, with_utxos[:MAX_FEE_OUTPUTS])


class IOAddressesStatic(IOAddresses):
    def __init__(self, i_addrs=None, o_addrs=None):
        self._iaddrs = i_addrs
        self._oaddrs = o_addrs

    def rotate(self):
        self._iaddrs, self._oaddrs = self._oaddrs, self._iaddrs

    def __call__(self, *args, **kwargs):
        return (self._iaddrs, self._oaddrs)


# ######################
# configuration fixtures
# ######################
8

@pytest.fixture(scope="module")
def fees(request):
    default_fees = {
        NYM_FEES_ALIAS: 4,
        XFER_PUBLIC_FEES_ALIAS: 8
    }
    fees = getValueFromModule(request, "TXN_FEES", default_fees)
    return fees


@pytest.fixture
def addresses_num(request):
    return getValueFromModule(request, "ADDRESSES_NUM", 2)


@pytest.fixture
def mint_strategy(request):
    return getValueFromModule(request, "MINT_STRATEGY", MintStrategy.first_only)


@pytest.fixture
def mint_utxos_num(request):
    return getValueFromModule(request, "MINT_UTXOS_NUM", 3)


@pytest.fixture
def mint_amount(request):
    return getValueFromModule(request, "MINT_AMOUNT", 1000)


@pytest.fixture
def inputs_strategy(request):
    return getValueFromModule(request, "INPUTS_STRATEGY", InputsStrategy.all_utxos)


@pytest.fixture
def outputs_strategy(request):
    return getValueFromModule(request, "OUTPUTS_STRATEGY", OutputsStrategy.transfer_some_equal)


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


@pytest.fixture()
def fees_set_with_batch(helpers, fees):
    helpers.general.set_fees_without_waiting(fees)
    result = helpers.general.do_set_fees(fees)
    return get_payload_data(result)


@pytest.fixture(scope="module")
def libsovtoken():
    libloader.load_libsovtoken()


@pytest.fixture(scope="module")
def sdk_wallet_steward(sdk_wallet_handle, sdk_stewards):
    return sdk_wallet_handle, sdk_stewards[0]


@pytest.fixture(scope="module")
def helpers(
    nodeSetWithIntegratedTokenPlugin,
    looper,
    sdk_pool_handle,
    trustee_wallets,
    steward_wallets,
    sdk_wallet_client,
    sdk_wallet_steward,
    libsovtoken,
    sdk_wallet_handle,
    sdk_trustees,
    sdk_stewards
):
    return form_helpers(
        nodeSetWithIntegratedTokenPlugin,
        looper,
        sdk_pool_handle,
        trustee_wallets,
        steward_wallets,
        sdk_wallet_client,
        sdk_wallet_steward,
        sdk_wallet_handle,
        sdk_trustees,
        sdk_stewards
    )


@pytest.fixture(autouse=True)
def reset_fees(helpers):
    helpers.node.reset_fees()


@pytest.fixture()
def address_main(helpers, libsovtoken):
    return helpers.wallet.create_address()


@pytest.fixture()
def address_main_inner(helpers, libsovtoken):
    return helpers.inner.wallet.create_address()



@pytest.fixture(scope="module")
def trustee_wallets(trustee_data, looper, sdk_pool_data):
    return build_wallets_from_data(trustee_data)


@pytest.fixture(scope="module")
def steward_wallets(poolTxnData):
    steward_data = get_data_for_role(poolTxnData, STEWARD)
    return build_wallets_from_data(steward_data)


@pytest.fixture()
def mint_tokens(helpers, address_main):
    return helpers.general.do_mint([
        {ADDRESS: address_main, AMOUNT: 1000},
    ])


@pytest.fixture()
def mint_tokens_inner(helpers, address_main_inner):
    return helpers.general.do_mint([
        {ADDRESS: "pay:sov:" + address_main_inner, AMOUNT: 1000},
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
def xfer_addresses(helpers, libsovtoken):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture
def addresses(helpers, addresses_num):
    return helpers.wallet.create_new_addresses(addresses_num)

@pytest.fixture
def mint_amount_spec(request, addresses, mint_strategy, mint_amount):
    amounts = {addr: 0 for addr in addresses}

    if mint_strategy == MintStrategy.first_only:
        amounts[addresses[0]] = mint_amount
    elif mint_strategy == MintStrategy.all_equal:
        amounts = {addr: mint_amount for addr in addresses}
    else:
        raise ValueError("unexpected mint strategy: {}".format(mint_strategy))

    return amounts


@pytest.fixture
def mint_utxos_num_spec(request, addresses, mint_utxos_num):
    return {addr: mint_utxos_num for addr in addresses}


@pytest.fixture
def mint_multiple_tokens(helpers, addresses, mint_utxos_num_spec, mint_amount_spec):
    res = []
    count = 0

    while True:
        _mints = [
            addr for addr in addresses
            if ((mint_utxos_num_spec[addr] > count) and mint_amount_spec[addr])
        ]
        if _mints:
            count += 1
            outputs = [
                {ADDRESS: addr, AMOUNT: mint_amount_spec[addr]} for addr in _mints
            ]
            res.append(helpers.general.do_mint(outputs))
        else:
            break

    for addr in addresses:
        helpers.wallet.handle_get_utxo_response(
            helpers.general.do_get_utxo(addr))

    return res


@pytest.fixture
def io_addresses(helpers, addresses):
    return IOAddressesDynamic(helpers, addresses)


@pytest.fixture
def prepare_inputs(helpers, inputs_strategy, io_addresses):
    _inputs_strategy = inputs_strategy

    def wrapped(addresses=None, inputs_strategy=None, txn_type=None):
        addresses = io_addresses(txn_type)[0] if addresses is None else addresses
        inputs_strategy = (
            _inputs_strategy if inputs_strategy is None else inputs_strategy
        )
        return prepare_inputs_h(helpers, addresses, strategy=inputs_strategy)

    return wrapped


@pytest.fixture
def prepare_outputs(
    helpers, outputs_strategy, transfer_amount,
    io_addresses, prepare_inputs, fees
):
    _outputs_strategy = outputs_strategy

    def wrapped(fee=None, txn_type=None, inputs=None, addresses=None, outputs_strategy=None):
        if txn_type is not None:
            fee = fees.get(txn_type_to_alias[txn_type], 0)

        inputs = prepare_inputs(txn_type=txn_type) if inputs is None else inputs
        addresses = io_addresses(txn_type)[1] if addresses is None else addresses
        outputs_strategy = (
            _outputs_strategy if outputs_strategy is None else outputs_strategy
        )

        return prepare_outputs_h(
            helpers, fee, inputs, addresses,
            strategy=outputs_strategy, transfer_amount=transfer_amount
        )

    return wrapped


@pytest.fixture
def send_and_check_xfer(
    looper, helpers, prepare_inputs, prepare_outputs, fees,
):
    def wrapped(inputs=None, outputs=None):
        inputs = prepare_inputs(txn_type=XFER_PUBLIC) if inputs is None else inputs
        outputs = prepare_outputs(txn_type=XFER_PUBLIC, inputs=inputs) if outputs is None else outputs
        res = send_and_check_xfer_h(looper, helpers, inputs, outputs)
        return res

    return wrapped


@pytest.fixture
def send_and_check_nym(
    looper, helpers, prepare_inputs, prepare_outputs, fees,
):
    def wrapped(inputs=None, outputs=None):
        inputs = prepare_inputs(txn_type=NYM) if inputs is None else inputs
        outputs = prepare_outputs(txn_type=NYM, inputs=inputs) if outputs is None else outputs
        res = send_and_check_nym_h(looper, helpers, inputs, outputs)
        return res

    return wrapped


# TODO old fixtures for backward compartibility
@pytest.fixture
def xfer_addresses(addresses):
    return addresses[:2]


@pytest.fixture
def xfer_mint_tokens(mint_multiple_tokens):
    return mint_multiple_tokens[0]


@pytest.fixture(scope="module")
def sdk_wallet_trustee(sdk_wallet_handle, sdk_trustees):
    return sdk_wallet_handle, sdk_trustees[0]


@pytest.fixture()
def increased_trustees(helpers, trustee_wallets, sdk_wallet_trustee):
    wallets = [helpers.inner.wallet.create_client_wallet() for _ in range(3)]

    def _nym_request_from_client_wallet(wallet):
        identifier = wallet.defaultId
        signer = wallet.idsToSigners[identifier]
        return helpers.request.nym(
            dest=identifier,
            verkey=signer.verkey,
            role=TRUSTEE_STRING,
            sdk_wallet=sdk_wallet_trustee
        )

    requests = map(_nym_request_from_client_wallet, wallets)

    responses = helpers.sdk.send_and_check_request_objects(requests)

    yield trustee_wallets + wallets

    def _update_nym_standard_user(response):
        data = get_payload_data(response[RESULT])
        request = helpers.request.nym(
            dest=data[TARGET_NYM],
            role='',
            sdk_wallet=sdk_wallet_trustee
        )
        return request

    requests = [
        _update_nym_standard_user(response)
        for _, response in responses
    ]

    helpers.sdk.send_and_check_request_objects(requests)
