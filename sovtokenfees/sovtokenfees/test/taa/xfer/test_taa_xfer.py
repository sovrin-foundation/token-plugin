import json
import time

import pytest
from indy.ledger import append_txn_author_agreement_acceptance_to_request

from plenum.common.exceptions import RequestNackedException


@pytest.fixture(scope="module")
def set_acceptance_mechanism(helpers, sdk_wallet_trustee):
    helpers.general.do_acceptance_mechanism(sdk_wallet_trustee, json.dumps({"aaa": "bbb"}))
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


def test_taa_xfer_positive_no_extra(helpers,
                                    address_main,
                                    addresses,
                                    mint_tokens,
                                    set_acceptance_mechanism,
                                    set_transaction_author_agreement):
    text, version = set_transaction_author_agreement
    inputs = helpers.general.get_utxo_addresses([address_main])[0]
    outputs = [{"address": addresses[1], "amount": 1000}]
    helpers.general.do_transfer(inputs, outputs, text=text, mechanism=set_acceptance_mechanism, version=version)


def test_taa_xfer_positive_with_extra(helpers,
                                      address_main,
                                      addresses,
                                      mint_tokens,
                                      set_acceptance_mechanism,
                                      set_transaction_author_agreement):
    text, version = set_transaction_author_agreement
    inputs = helpers.general.get_utxo_addresses([address_main])[0]
    outputs = [{"address": addresses[1], "amount": 1000}]
    helpers.general.do_transfer(inputs, outputs, extra=json.dumps({"aaa": "bbb"}), text=text,
                                mechanism=set_acceptance_mechanism, version=version)


def test_taa_xfer_negative_not_signed(helpers,
                                      address_main,
                                      addresses,
                                      mint_tokens,
                                      set_acceptance_mechanism,
                                      set_transaction_author_agreement,
                                      looper):
    text, version = set_transaction_author_agreement
    inputs = helpers.general.get_utxo_addresses([address_main])[0]
    outputs = [{"address": addresses[1], "amount": 1000}]
    request = helpers.request.transfer(inputs, outputs)
    request = json.dumps(request.as_dict)
    request_future = append_txn_author_agreement_acceptance_to_request(request,
                                                                       text,
                                                                       version,
                                                                       None,
                                                                       set_acceptance_mechanism,
                                                                       round(time.time()))
    request = looper.loop.run_until_complete(request_future)
    with pytest.raises(RequestNackedException):
        helpers.sdk.sdk_send_and_check([request])
