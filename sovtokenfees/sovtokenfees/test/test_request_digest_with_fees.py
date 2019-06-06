import copy
import json

import pytest
from plenum.test.pool_transactions.helper import prepare_nym_request
from sovtokenfees.test.helper import nyms_with_fees, get_amount_from_token_txn

from plenum.common.exceptions import RequestNackedException
from plenum.common.util import randomString

from plenum.test.helper import sdk_get_and_check_replies, sdk_sign_request_objects, \
    sdk_json_to_request_object


@pytest.fixture(scope='function')
def two_requests(looper, helpers,
                 nodeSetWithIntegratedTokenPlugin,
                 sdk_pool_handle,
                 fees_set, address_main, mint_tokens, sdk_wallet_steward):
    amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1

    seed = randomString(32)
    alias = randomString(5)
    wh, _ = sdk_wallet_steward
    nym_request, new_did = looper.loop.run_until_complete(
        prepare_nym_request(sdk_wallet_steward, seed,
                            alias, None))
    nym_request = \
        sdk_sign_request_objects(looper, sdk_wallet_steward, [sdk_json_to_request_object(json.loads(nym_request))])[0]
    req_obj = sdk_json_to_request_object(json.loads(nym_request))
    helpers.request.nym = lambda: copy.deepcopy(req_obj)

    req1, req2 = nyms_with_fees(2,
                                helpers,
                                fees_set,
                                address_main,
                                amount,
                                init_seq_no=init_seq_no)

    assert req1.payload_digest == req2.payload_digest
    assert req1.digest != req2.digest
    return req1, req2


def test_send_same_txn_with_different_fees(helpers, looper, nodeSetWithIntegratedTokenPlugin,
                                           sdk_pool_handle, two_requests):
    req1, req2 = two_requests

    resp = helpers.sdk.send_request_objects([req1], )
    sdk_get_and_check_replies(looper, resp)

    resp = helpers.sdk.send_request_objects([req2])
    with pytest.raises(RequestNackedException) as e:
        sdk_get_and_check_replies(looper, resp)
    e.match('Same txn was already ordered with different signatures or pluggable fields')
