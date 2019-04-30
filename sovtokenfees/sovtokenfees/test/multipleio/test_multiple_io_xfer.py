import pytest

from sovtoken.constants import XFER_PUBLIC


@pytest.fixture(
    scope='module',
    params=[
        {XFER_PUBLIC: 0},  # no fees
        {XFER_PUBLIC: 4},  # with fees
    ], ids=lambda x: 'fees' if x[XFER_PUBLIC] else 'nofees'
)
def fees(request):
    return request.param


def test_xfer_with_multiple_io(
    nodeSetWithIntegratedTokenPlugin,
    fees_set,
    mint_multiple_tokens,
    io_addresses,
    send_and_check_xfer,
):
    send_and_check_xfer()
    io_addresses.rotate()
    send_and_check_xfer()
