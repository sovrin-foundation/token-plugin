import pytest

from plenum.common.exceptions import RequestNackedException

from indy_common.constants import NYM

from sovtokenfees.constants import MAX_FEE_OUTPUTS
from sovtokenfees.test.helper import OutputsStrategy


@pytest.fixture(
    scope='module',
    params=[
        {NYM: 4},  # with fees
    ], ids=lambda x: 'fees' if x[NYM] else 'nofees'
)
def fees(request):
    return request.param


def test_nym_with_multiple_io(
    nodeSetWithIntegratedTokenPlugin,
    fees_set,
    mint_multiple_tokens,
    io_addresses,
    outputs_strategy,
    send_and_check_nym,
):
    def send():
        if (
            len(io_addresses.oaddrs) > MAX_FEE_OUTPUTS or
            (   # some change goes to some input
                outputs_strategy != OutputsStrategy.transfer_all_equal and
                io_addresses.oaddrs != io_addresses.iaddrs
            )
        ):
            with pytest.raises(
                RequestNackedException,
                match=(r".*length should be at most {}.*"
                       .format(MAX_FEE_OUTPUTS))
            ):
                send_and_check_nym()
        else:
            send_and_check_nym()

    send()
    io_addresses.rotate()
    send()
