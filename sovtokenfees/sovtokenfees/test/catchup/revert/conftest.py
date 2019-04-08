import pytest
from sovtoken.constants import ADDRESS, AMOUNT, XFER_PUBLIC

from plenum.common.constants import NYM
from plenum.test.conftest import getValueFromModule


@pytest.fixture()
def xfer_addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def xfer_mint_tokens(helpers, xfer_addresses):
    outputs = [{ADDRESS: xfer_addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


@pytest.fixture(scope="module", params=[True, False])
def fees(request):
    default_fees = {NYM: 4, XFER_PUBLIC: 0}
    if request.param:
        default_fees[XFER_PUBLIC] = 8

    fees = getValueFromModule(request, "TXN_FEES", default_fees)
    return fees
