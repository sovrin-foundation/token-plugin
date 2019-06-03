import json

import pytest
from sovtoken.sovtoken_auth_map import sovtoken_auth_map
from sovtoken import TokenTransactions, TOKEN_LEDGER_ID
from sovtoken.request_handlers.write_request_handler.mint_handler import MintHandler

from indy.payment import build_mint_req
from indy.did import create_and_store_my_did
from indy.ledger import multi_sign_request

from plenum.common.txn_util import append_txn_metadata
from plenum.test.helper import sdk_json_to_request_object

from indy_common.test.auth.conftest import write_auth_req_validator, constraint_serializer, config_state
from plenum.test.testing_utils import FakeSomething


@pytest.fixture(scope="module")
def mint_handler(utxo_cache, db_manager, write_auth_req_validator):
    write_auth_req_validator.auth_map.update(sovtoken_auth_map)
    return MintHandler(database_manager=db_manager,
                       txn_type=TokenTransactions.MINT_PUBLIC.value,
                       ledger_id=TOKEN_LEDGER_ID,
                       write_req_validator=write_auth_req_validator,
                       state=db_manager.get_state(TOKEN_LEDGER_ID),
                       utxo_cache=utxo_cache)


@pytest.fixture(scope="module")
def idr_cache():
    idr_cache = FakeSomething()
    idr_cache.users = {}

    def getRole(idr, isCommitted=True):
        return idr_cache.users.get(idr, None)

    idr_cache.getRole = getRole
    return idr_cache


@pytest.fixture()
def mint_request(libsovtoken, payment_address, wallet, trustees, looper):
    mint_future = build_mint_req(wallet,
                                 trustees[0],
                                 json.dumps([{"recipient": payment_address, "amount": 10}]),
                                 None)
    mint_request, _ = looper.loop.run_until_complete(mint_future)
    for trustee in trustees:
        mint_future = multi_sign_request(wallet, trustee, mint_request)
        mint_request = looper.loop.run_until_complete(mint_future)
    mint_request = json.loads(mint_request)
    sigs = mint_request["signatures"]
    mint_request = sdk_json_to_request_object(mint_request)
    setattr(mint_request, "signatures", sigs)
    return mint_request


@pytest.fixture()
def mint_txn(mint_handler, mint_request):
    mint_txn = mint_handler._req_to_txn(mint_request)
    return append_txn_metadata(mint_txn, 1, 1, 1)


@pytest.fixture(scope="module")
def trustees(libsovtoken, wallet, looper, idr_cache):
    trustees = []
    for i in range(3):
        did_future = create_and_store_my_did(wallet, "{}")
        did, vk = looper.loop.run_until_complete(did_future)
        trustees.append(did)
        idr_cache.users[did] = "0"
    return trustees
