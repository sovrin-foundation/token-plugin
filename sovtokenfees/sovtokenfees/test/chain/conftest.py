import pytest
from sovtoken.constants import ADDRESS, AMOUNT


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(4)


@pytest.fixture()
def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)