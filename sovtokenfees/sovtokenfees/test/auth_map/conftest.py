import pytest


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(4)