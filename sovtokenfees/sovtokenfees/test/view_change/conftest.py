import pytest

from plenum.test.conftest import getValueFromModule

from sovtokenfees.test.helper import InputsStrategy
from sovtokenfees.test.conftest import MintStrategy


@pytest.fixture
def addresses_num(request):
    return getValueFromModule(request, "ADDRESSES_NUM", 4)


@pytest.fixture
def mint_strategy(request):
    return getValueFromModule(request, "MINT_STRATEGY", MintStrategy.all_equal)


@pytest.fixture
def inputs_strategy(request):
    return getValueFromModule(request, "INPUTS_STRATEGY", InputsStrategy.first_utxo_only)
