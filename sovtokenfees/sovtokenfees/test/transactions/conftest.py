import json

import pytest
from indy.ledger import build_get_schema_request, parse_get_schema_response
from indy_node.test.api.helper import sdk_write_schema

from indy_common.types import Request

from plenum.common.constants import TXN_METADATA, TXN_METADATA_ID
from plenum.test.helper import sdk_get_reply, sdk_sign_and_submit_req


@pytest.fixture(scope="module")
def schema_json(looper, sdk_pool_handle, sdk_wallet_trustee):
    wallet_handle, identifier = sdk_wallet_trustee
    schema_json, _ = sdk_write_schema(looper, sdk_pool_handle, sdk_wallet_trustee)
    schema_id = json.loads(schema_json)['id']

    request = looper.loop.run_until_complete(build_get_schema_request(identifier, schema_id))
    reply = sdk_get_reply(looper, sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request))[1]
    _, schema_json = looper.loop.run_until_complete(parse_get_schema_response(json.dumps(reply)))
    return schema_json


@pytest.fixture()
def claim_def_id(helpers,
                 schema_json,
                 sdk_wallet_trustee):
    req = helpers.request.claim_def(schema_json, sdk_wallet=sdk_wallet_trustee)
    req = Request(**json.loads(req))
    write_rep = helpers.sdk.send_and_check_request_objects([req], wallet=sdk_wallet_trustee)
    return write_rep[0][1]['result'][TXN_METADATA][TXN_METADATA_ID]
