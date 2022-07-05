import json

import pytest
from indy.ledger import multi_sign_request
from indy.payment import build_set_txn_fees_req
from sovtokenfees.sovtokenfees_auth_map import sovtokenfees_auth_map
from sovtokenfees.req_handlers.write_handlers.set_fees_handler import SetFeesHandler
from sovtoken.test.req_handlers.mint_req_handler.conftest import trustees
from sovtoken.test.req_handlers.conftest import wallet

from indy_node.test.conftest import write_auth_req_validator, constraint_serializer, config_state
from plenum.common.txn_util import append_txn_metadata
from plenum.test.helper import sdk_json_to_request_object
from plenum.test.testing_utils import FakeSomething


@pytest.fixture(scope="module")
def set_fees_handler(db_manager_with_config, write_auth_req_validator):  # noqa: F811
    write_auth_req_validator.auth_map.update(sovtokenfees_auth_map)
    return SetFeesHandler(db_manager_with_config, write_auth_req_validator)


@pytest.fixture(scope="module")
def idr_cache():
    idr_cache = FakeSomething()
    idr_cache.users = {}

    def getRole(idr, isCommitted=True):
        return idr_cache.users.get(idr, None)

    idr_cache.getRole = getRole
    return idr_cache


@pytest.fixture()
def set_fees_request(libsovtoken, looper, trustees, wallet, fees):  # noqa: F811
    set_fees_future = build_set_txn_fees_req(wallet,
                                             trustees[0],
                                             "sov",
                                             fees)
    set_fees_request = looper.loop.run_until_complete(set_fees_future)
    for trustee in trustees:
        set_fees_future = multi_sign_request(wallet, trustee, set_fees_request)
        set_fees_request = looper.loop.run_until_complete(set_fees_future)
    set_fees_request = json.loads(set_fees_request)
    sigs = set_fees_request["signatures"]
    set_fees_request = sdk_json_to_request_object(set_fees_request)
    setattr(set_fees_request, "signatures", sigs)
    return set_fees_request


@pytest.fixture()
def set_fees_txn(set_fees_request, set_fees_handler):
    set_fees_txn = set_fees_handler._req_to_txn(set_fees_request)
    return append_txn_metadata(set_fees_txn, 1, 1, 1)
