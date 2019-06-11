import json

import pytest
from indy.payment import build_get_txn_fees_req
from sovtokenfees.domain import build_path_for_set_fees
from sovtokenfees.req_handlers.read_handlers.get_fees_handler import GetFeesHandler

from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.test.helper import sdk_json_to_request_object
from sovtoken.test.req_handlers.conftest import wallet


@pytest.fixture(scope="module")
def get_fees_handler(db_manager, bls_store):
    return GetFeesHandler(db_manager)


@pytest.fixture(scope="module")
def prepare_fees(db_manager, fees):
    config_state = db_manager.get_state(CONFIG_LEDGER_ID)
    path = build_path_for_set_fees()
    config_state.set(path.encode(), fees)


@pytest.fixture()
def get_fees_request(looper, libsovtoken, wallet):
    get_fees_future = build_get_txn_fees_req(wallet, None, "sov")
    get_fees_request = looper.loop.run_until_complete(get_fees_future)
    get_fees_request = sdk_json_to_request_object(json.loads(get_fees_request))
    return get_fees_request
