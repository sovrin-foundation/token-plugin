import json

import pytest
from sovtoken.constants import AMOUNT
from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no
from sovtokenfees.test.constants import REVOC_REG_DEF_FEES_ALIAS
from sovtokenfees.test.helper import get_amount_from_token_txn, add_fees_request_with_address

from indy_common.types import Request
from plenum.common.constants import TXN_METADATA, TXN_METADATA_ID, DATA
from plenum.test.helper import sdk_get_and_check_replies, sdk_sign_and_submit_req


@pytest.fixture()
def fees():
    return {REVOC_REG_DEF_FEES_ALIAS: 5}

@pytest.fixture()
def claim_def(helpers,
              schema_json,
              sdk_wallet_trustee):
    req = helpers.request.claim_def(schema_json, sdk_wallet=sdk_wallet_trustee)
    write_rep = helpers.sdk.send_and_check_request_objects([req], wallet=sdk_wallet_trustee)
    return write_rep[0][1]['result'][TXN_METADATA][TXN_METADATA_ID]


def test_revoc_reg_def_with_fees(helpers,
                                  looper,
                                  nodeSetWithIntegratedTokenPlugin,
                                  sdk_wallet_trustee,
                                  sdk_pool_handle,
                                  claim_def,
                                  fees_set, address_main, mint_tokens):
    req = helpers.request.revoc_reg_def(schema_json, sdk_wallet=sdk_wallet_trustee)
    amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1
    utxos = [{"source": utxo_from_addr_and_seq_no(address_main, init_seq_no),
              AMOUNT: amount}]
    req = Request(**json.loads(req))
    req = add_fees_request_with_address(
        helpers,
        fees_set,
        req,
        address_main,
        utxos=utxos
    )
    write_rep = helpers.sdk.send_and_check_request_objects([req], wallet=sdk_wallet_trustee)
    added_claim_def_id = write_rep[0][1]['result'][TXN_METADATA][TXN_METADATA_ID]
    request = looper.loop.run_until_complete(build_get_cred_def_request(sdk_wallet_trustee[1], added_claim_def_id))
    read_rep = sdk_get_and_check_replies(looper,
                                         [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])
    assert req.operation[DATA] == read_rep[0][1]['result'][DATA]

