import pytest
from sovtoken.constants import ADDRESS, AMOUNT

from indy_node.test.pool_config.conftest import poolConfigWTFF


@pytest.fixture()
def xfer_addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture()
def xfer_mint_tokens(helpers, xfer_addresses):
    outputs = [{ADDRESS: xfer_addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)
