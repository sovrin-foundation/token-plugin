import json

import pytest

from sovtoken import TOKEN_LEDGER_ID, TokenTransactions
from sovtoken.request_handlers.read_req_handler.get_utxo_handler import GetUtxoHandler

from plenum.test.helper import sdk_json_to_request_object

from indy.payment import build_get_payment_sources_request


@pytest.fixture(scope="module")
def get_utxo_handler(db_manager, bls_store):
    return GetUtxoHandler(bls_store=bls_store, database_manager=db_manager)


@pytest.fixture()
def get_utxo_request(looper, payment_address, wallet):
    get_utxo_request_future = build_get_payment_sources_request(wallet, None, payment_address)
    get_utxo_request, _ = looper.loop.run_until_complete(get_utxo_request_future)
    get_utxo_request = json.loads(get_utxo_request)
    get_utxo_request = sdk_json_to_request_object(get_utxo_request)
    return get_utxo_request
