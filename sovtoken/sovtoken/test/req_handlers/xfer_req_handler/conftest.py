import json

import pytest
from sovtoken import TokenTransactions, TOKEN_LEDGER_ID
from sovtoken.request_handlers.write_request_handler.xfer_handler import XferHandler
from sovtoken.sovtoken_auth_map import sovtoken_auth_map
from base58 import b58encode_check
from indy.payment import build_payment_req
from indy_node.test.conftest import write_auth_req_validator, constraint_serializer, config_state, idr_cache
from plenum.common.txn_util import append_txn_metadata
from plenum.test.helper import sdk_json_to_request_object


@pytest.fixture(scope="module")
def xfer_handler(utxo_cache, db_manager, write_auth_req_validator, mint_tokens):
    write_auth_req_validator.auth_map.update(sovtoken_auth_map)
    return XferHandler(db_manager,
                       write_req_validator=write_auth_req_validator)


@pytest.fixture(scope="module")
def mint_tokens(payment_address, utxo_cache, db_manager):
    addr = libsovtoken_address_to_address(payment_address)
    utxo_cache.set(addr, "1:10".encode())
    db_manager.get_state(TOKEN_LEDGER_ID).set((addr + ":1").encode(), "10".encode())


@pytest.fixture()
def xfer_request(libsovtoken, payment_address, payment_address_2, wallet, looper):
    input = make_utxo(payment_address, 1)
    output = payment_address_2
    xfer_request_future = build_payment_req(wallet, None, json.dumps([input]),
                                            json.dumps([{"recipient": output, "amount": 10}]), None)
    xfer_request, _ = looper.loop.run_until_complete(xfer_request_future)
    xfer_request = sdk_json_to_request_object(json.loads(xfer_request))
    return xfer_request


@pytest.fixture()
def invalid_amount_xfer_request_insufficient(libsovtoken, payment_address, payment_address_2, wallet, looper):
    input = make_utxo(payment_address, 1)
    output = payment_address_2
    xfer_request_future = build_payment_req(wallet, None, json.dumps([input]),
                                            json.dumps([{"recipient": output, "amount": 11}]), None)
    xfer_request, _ = looper.loop.run_until_complete(xfer_request_future)
    xfer_request = sdk_json_to_request_object(json.loads(xfer_request))
    return xfer_request


@pytest.fixture()
def invalid_amount_xfer_request_excessive(libsovtoken, payment_address, payment_address_2, wallet, looper):
    input = make_utxo(payment_address, 1)
    output = payment_address_2
    xfer_request_future = build_payment_req(wallet, None, json.dumps([input]),
                                            json.dumps([{"recipient": output, "amount": 9}]), None)
    xfer_request, _ = looper.loop.run_until_complete(xfer_request_future)
    xfer_request = sdk_json_to_request_object(json.loads(xfer_request))
    return xfer_request


@pytest.fixture()
def invalid_amount_xfer_request_utxo_does_not_exist(libsovtoken, payment_address, payment_address_2, wallet, looper):
    input = make_utxo(payment_address, 2)
    output = payment_address_2
    xfer_request_future = build_payment_req(wallet, None, json.dumps([input]),
                                            json.dumps([{"recipient": output, "amount": 9}]), None)
    xfer_request, _ = looper.loop.run_until_complete(xfer_request_future)
    xfer_request = sdk_json_to_request_object(json.loads(xfer_request))
    return xfer_request


@pytest.fixture()
def xfer_txn(xfer_handler, xfer_request):
    xfer_txn = xfer_handler._req_to_txn(xfer_request)
    return append_txn_metadata(xfer_txn, 2, 1, 1)


def make_utxo(addr, seq_no):
    txo_inner = json.dumps({"address": addr, "seqNo": seq_no})
    return "{}{}". format("txo:sov:", b58encode_check(txo_inner.encode()).decode())
