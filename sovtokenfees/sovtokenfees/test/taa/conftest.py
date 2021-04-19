import json

import pytest
from sovtoken.constants import ADDRESS, AMOUNT


@pytest.fixture(scope="module")
def set_acceptance_mechanism(helpers, sdk_wallet_trustee):
    helpers.general.do_acceptance_mechanism(sdk_wallet_trustee, json.dumps({"aaa": "bbb"}), "aml_context")
    return "aaa"


@pytest.fixture(scope="module")
def set_transaction_author_agreement(helpers, sdk_wallet_trustee):
    helpers.general.do_transaction_author_agreement(sdk_wallet_trustee, "test taa", "abc")
    return "test taa", "abc"


@pytest.fixture()
def get_transaction_author_agreement(helpers, set_transaction_author_agreement):
    # TODO: this is not implemented yet, so not working
    # return helpers.general.do_get_transaction_author_agreement()
    pass


@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(4)


@pytest.fixture()
def mint_tokens(helpers, addresses, set_acceptance_mechanism, set_transaction_author_agreement):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    text, version = set_transaction_author_agreement
    return helpers.general.do_mint(outputs, text=text, mechanism=set_acceptance_mechanism, version=version)


@pytest.fixture()
def mint_tokens_no_taa(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)
