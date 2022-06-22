import json

import pytest
from indy_node.test.request_handlers.helper import get_fake_ledger
from sovtoken import TOKEN_LEDGER_ID
from sovtokenfees.constants import FEES
from sovtokenfees.req_handlers.write_handlers.domain_fee_handler import DomainFeeHandler
from sovtoken.test.req_handlers.conftest import utxo_cache, wallet, payment_address
from sovtoken.test.req_handlers.mint_req_handler.conftest import trustees, idr_cache
from sovtoken.test.req_handlers.xfer_req_handler.conftest import mint_tokens

from common.serializers import serialization
from plenum.common.constants import NYM, DOMAIN_LEDGER_ID, KeyValueStorageType
from indy.did import create_and_store_my_did
from indy.ledger import build_nym_request
from indy.payment import add_request_fees
from base58 import b58encode_check

from plenum.common.txn_util import append_txn_metadata
from plenum.test.helper import sdk_json_to_request_object
from state.pruning_state import PruningState
from storage.helper import initKeyValueStorage


@pytest.fixture(scope="module")
def domain_fee_handler(db_manager_with_config, fees_tracker, utxo_cache, mint_tokens):  # noqa: F811
    handler = DomainFeeHandler(db_manager_with_config, fees_tracker)
    handler.txn_type = NYM
    return handler


@pytest.fixture()
def nym_request(wallet, looper, trustees):  # noqa: F811
    did_future = create_and_store_my_did(wallet, "{}")
    did, vk = looper.loop.run_until_complete(did_future)
    nym_future = build_nym_request(trustees[0], did, vk, None, None)
    nym_req = looper.loop.run_until_complete(nym_future)
    return nym_req


@pytest.fixture()
def nym_request_with_fees(libsovtoken, nym_request, wallet, payment_address, looper):  # noqa: F811
    inputs = json.dumps(
        ["txo:sov:" + b58encode_check(json.dumps({"address": payment_address, "seqNo": 1}).encode()).decode()])
    outputs = json.dumps([{
        "recipient": payment_address,
        "amount": 9
    }])
    fees_future = add_request_fees(wallet, None, nym_request, inputs, outputs, None)
    fees, _ = looper.loop.run_until_complete(fees_future)
    fees_req = json.loads(fees)
    fees = fees_req[FEES]
    fees_req = sdk_json_to_request_object(fees_req)
    setattr(fees_req, FEES, fees)
    return fees_req


@pytest.fixture()
def nym_txn(domain_fee_handler, nym_request):
    nym_request = sdk_json_to_request_object(json.loads(nym_request))
    nym_txn = domain_fee_handler._req_to_txn(nym_request)
    return append_txn_metadata(nym_txn, 1, 1, 1)
