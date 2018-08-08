import json

from plenum.common.constants import NYM
from plenum.common.util import randomString
from sovtokenfees.test.helper import gen_nym_req_for_fees
from sovtoken.constants import XFER_PUBLIC
from plenum.test.helper import sdk_send_signed_requests, sdk_get_replies
from plenum.test.pool_transactions.helper import sdk_add_new_nym

TXN_FEES = {
    NYM: 0,
    XFER_PUBLIC: 8
}


def test_txn_with_no_fees_specified(tokens_distributed, looper, sdk_wallet_steward,  # noqa
                                    sdk_pool_handle, fees_set,
                                    user1_address, user1_token_wallet):
    name = randomString(6)
    sdk_add_new_nym(looper, sdk_pool_handle, sdk_wallet_steward, alias=name)


def test_txn_with_0_fees_specified(tokens_distributed, looper, sdk_wallet_steward,  # noqa
                                   sdk_pool_handle, fees_set,
                                   user1_address, user1_token_wallet):
    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    req = user1_token_wallet.add_fees_to_request(req, fee_amount=0,
                                                 address=user1_address)
    res = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(req.__dict__)])
    assert sdk_get_replies(looper, res, timeout=20)
