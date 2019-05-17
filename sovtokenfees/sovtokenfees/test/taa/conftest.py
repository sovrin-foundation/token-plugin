import json

import pytest


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

