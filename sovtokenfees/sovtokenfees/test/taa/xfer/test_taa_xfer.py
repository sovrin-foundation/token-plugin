import json
import time

import pytest
from indy.ledger import append_txn_author_agreement_acceptance_to_request

from plenum.common.exceptions import RequestNackedException, RequestRejectedException


def test_taa_xfer_positive_no_extra(helpers,
                                    addresses,
                                    mint_tokens,
                                    set_acceptance_mechanism,
                                    set_transaction_author_agreement):
    time.sleep(5)
    text, version = set_transaction_author_agreement
    inputs = helpers.general.get_utxo_addresses([addresses[0]])[0]
    outputs = [{"address": addresses[1], "amount": 1000}]
    helpers.general.do_transfer(inputs, outputs, text=text, mechanism=set_acceptance_mechanism, version=version)


def test_taa_xfer_positive_with_extra(helpers,
                                      addresses,
                                      mint_tokens,
                                      set_acceptance_mechanism,
                                      set_transaction_author_agreement):
    text, version = set_transaction_author_agreement
    inputs = helpers.general.get_utxo_addresses([addresses[0]])[0]
    outputs = [{"address": addresses[1], "amount": 1000}]
    helpers.general.do_transfer(inputs, outputs, extra=json.dumps({"aaa": "bbb"}), text=text,
                                mechanism=set_acceptance_mechanism, version=version)


def test_taa_xfer_negative_not_signed(helpers,
                                      addresses,
                                      mint_tokens,
                                      set_acceptance_mechanism,
                                      set_transaction_author_agreement,
                                      looper):
    text, version = set_transaction_author_agreement
    inputs = helpers.general.get_utxo_addresses([addresses[0]])[0]
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


def test_taa_set_xfer_not_accepted(helpers,
                                   addresses,
                                   mint_tokens,
                                   set_acceptance_mechanism,
                                   set_transaction_author_agreement):
    inputs = helpers.general.get_utxo_addresses(addresses[:1])[0]
    outputs = [{"address": addresses[1], "amount": 1000}]
    with pytest.raises(RequestRejectedException):
        helpers.general.do_transfer(inputs, outputs)
