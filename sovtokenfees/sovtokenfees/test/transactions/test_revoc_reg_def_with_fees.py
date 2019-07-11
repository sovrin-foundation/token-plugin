import json

import pytest
from indy.ledger import build_get_revoc_reg_def_request
from sovtoken.constants import AMOUNT
from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no
from sovtokenfees.test.constants import REVOC_REG_DEF_FEES_ALIAS
from sovtokenfees.test.helper import get_amount_from_token_txn, add_fees_request_with_address

from indy_common.types import Request
from sovtokenfees.test.transactions.helper import get_last_token_txn

from plenum.common.constants import TXN_METADATA, TXN_METADATA_ID, DATA, TXN_TYPE
from plenum.test.helper import sdk_get_and_check_replies, sdk_sign_and_submit_req

REVOC_REG_DEF_FEE = 5


@pytest.fixture()
def fees():
    return {REVOC_REG_DEF_FEES_ALIAS: REVOC_REG_DEF_FEE}


def test_revoc_reg_def_with_fees(helpers,
                                 looper,
                                 nodeSetWithIntegratedTokenPlugin,
                                 sdk_wallet_trustee,
                                 sdk_pool_handle,
                                 claim_def_id,
                                 fees_set, address_main, mint_tokens):
    req = helpers.request.revoc_reg_def(claim_def_id, sdk_wallet=sdk_wallet_trustee)
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

    token_len = len(nodeSetWithIntegratedTokenPlugin[0].ledgers[-1])
    write_rep = helpers.sdk.send_and_check_request_objects([req], wallet=sdk_wallet_trustee)
    assert token_len == len(nodeSetWithIntegratedTokenPlugin[0].ledgers[-1]) - 1
    assert get_last_token_txn(nodeSetWithIntegratedTokenPlugin)[1]['txn']['data']['fees'] == REVOC_REG_DEF_FEE

    added_revoc_reg_def_id = write_rep[0][1]['result'][TXN_METADATA][TXN_METADATA_ID]
    request = looper.loop.run_until_complete(
        build_get_revoc_reg_def_request(sdk_wallet_trustee[1], added_revoc_reg_def_id))
    read_rep = sdk_get_and_check_replies(looper,
                                         [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])
    read_data = read_rep[0][1]['result'][DATA]
    req.operation.pop(TXN_TYPE)
    assert req.operation == read_data
