import pytest

from sovtokenfees.test.conftest import MintStrategy
from sovtokenfees.test.helper import InputsStrategy, OutputsStrategy


@pytest.fixture
def addresses_num():
    return 4


@pytest.fixture
def mint_strategy():
    return MintStrategy.multiple_equal


@pytest.fixture
def mint_utxos_num():
    return 3


@pytest.fixture
def mint_amount():
    return 1000


@pytest.fixture(params=InputsStrategy, ids=lambda x: x.name)
def inputs_strategy(request):
    return request.param


@pytest.fixture(params=OutputsStrategy, ids=lambda x: x.name)
def outputs_strategy(request):
    return request.param


@pytest.fixture
def transfer_amount():
    return 10


class IOAddresses:
    def __init__(self, i_addrs, o_addrs):
        self.i_addrs = i_addrs
        self.o_addrs = o_addrs

    def rotate(self):
        self.i_addrs, self.o_addrs = self.o_addrs, self.i_addrs

    def __call__(self):
        return (self.i_addrs, self.o_addrs)


@pytest.fixture(
    params=[
        ([0], [0]),
        ([0], [1]),
        ([0, 1], [2, 3]),
        ([0, 1, 2], [1, 2, 3]),
    ], ids=lambda x: (
        "i{}_o{}"
        .format(':'.join((map(str, x[0]))), ':'.join((map(str, x[1]))))
    )
)
def io_addresses(request, addresses):
    return IOAddresses(
        [addresses[i] for i in request.param[0]],
        [addresses[i] for i in request.param[1]]
    )
