import pytest

from plenum.test.conftest import getValueFromModule

from sovtoken.constants import ADDRESS, AMOUNT

from sovtokenfees.test.helper import InputsStrategy
from sovtokenfees.test.conftest import MintStrategy


@pytest.fixture()
def xfer_addresses(helpers, libsovtoken):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def xfer_mint_tokens(helpers, xfer_addresses):
    outputs = [{ADDRESS: xfer_addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


@pytest.fixture
def addresses_num(request):
    return getValueFromModule(request, "ADDRESSES_NUM", 4)


@pytest.fixture
def mint_strategy(request):
    return getValueFromModule(request, "MINT_STRATEGY", MintStrategy.all_equal)


@pytest.fixture
def inputs_strategy(request):
    return getValueFromModule(request, "INPUTS_STRATEGY", InputsStrategy.first_utxo_only)
