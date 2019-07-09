import json

import pytest
from indy.ledger import build_get_nym_request
from indy_common.types import Request
from sovtoken.constants import AMOUNT
from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no
from sovtokenfees.test.constants import NYM_FEES_ALIAS
from sovtokenfees.test.helper import get_amount_from_token_txn, add_fees_request_with_address

from plenum.common.constants import DATA
from plenum.test.helper import sdk_sign_and_submit_req, \
    sdk_get_and_check_replies


@pytest.fixture()
def fees():
    return {NYM_FEES_ALIAS: 5}


def test_send_nym_with_fees(helpers,
                            looper,
                            nodeSetWithIntegratedTokenPlugin,
                            sdk_wallet_trustee,
                            sdk_wallet_steward,
                            sdk_pool_handle,
                            fees_set, address_main, mint_tokens):
    req = helpers.request.nym(sdk_wallet=sdk_wallet_trustee)
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
    helpers.sdk.send_and_check_request_objects([req], wallet=sdk_wallet_trustee)
    request = looper.loop.run_until_complete(
        build_get_nym_request(sdk_wallet_trustee[1], req.operation['dest']))
    read_rep = sdk_get_and_check_replies(looper,
                                         [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])
    reply = json.loads(read_rep[0][1]['result'][DATA])
    assert req.operation['dest'] == reply['dest']
    assert req.operation['verkey'] == reply['verkey']
