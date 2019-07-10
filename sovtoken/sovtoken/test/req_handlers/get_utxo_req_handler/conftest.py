import json

import pytest

from sovtoken import TOKEN_LEDGER_ID, TokenTransactions
from sovtoken.constants import FROM_SEQNO
from sovtoken.request_handlers.read_req_handler.get_utxo_handler import GetUtxoHandler
from sovtoken.request_handlers.token_utils import TokenStaticHelper
from sovtoken.test.helper import libsovtoken_address_to_address

from plenum.test.helper import sdk_json_to_request_object

from indy.payment import build_get_payment_sources_request


@pytest.fixture(scope="module")
def get_utxo_handler(db_manager, bls_store):
    return GetUtxoHandler(database_manager=db_manager)


@pytest.fixture()
def get_utxo_request(looper, payment_address, wallet):
    get_utxo_request_future = build_get_payment_sources_request(wallet, None, payment_address)
    get_utxo_request, _ = looper.loop.run_until_complete(get_utxo_request_future)
    get_utxo_request = json.loads(get_utxo_request)
    get_utxo_request = sdk_json_to_request_object(get_utxo_request)
    return get_utxo_request


FROM_SHIFT = 200


@pytest.fixture()
def get_utxo_request_with_from(get_utxo_request):
    get_utxo_request.operation[FROM_SEQNO] = FROM_SHIFT
    return get_utxo_request


@pytest.fixture(scope="module")
def insert_over_thousand_utxos(db_manager, payment_address):
    token_state = db_manager.get_state(TOKEN_LEDGER_ID)
    for i in range(1200):
        token_state.set(TokenStaticHelper.create_state_key(libsovtoken_address_to_address(payment_address), i), str(i).encode())