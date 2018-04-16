import json

from plenum.common.constants import TXN_TYPE
from plenum.common.util import randomString
from plenum.server.plugin.fees import FEE, FEES, GET_FEES
from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies, sdk_gen_request, \
    sdk_sign_and_submit_req_obj, sdk_sign_request_objects, \
    sdk_json_to_request_object
from plenum.test.pool_transactions.helper import prepare_nym_request


def set_fees_request(trustees, fees):
    signatures = {}
    op = {
        TXN_TYPE: FEE,
        FEES: fees,
    }
    first_trustee = trustees[0]
    request = first_trustee.sign_using_multi_sig(
        op, identifier=first_trustee.defaultId)
    for wallet in trustees[1:]:
        signatures[wallet.defaultId] = wallet.do_multi_sig_on_req(
            request, identifier=wallet.defaultId)
    return request


def send_set_fees(looper, trustees, fees, sdk_pool_handle):
    request = set_fees_request(trustees, fees)
    request = sdk_send_signed_requests(sdk_pool_handle,
                                       [json.dumps(request.as_dict), ])
    return sdk_get_and_check_replies(looper, request)


def set_fees(looper, trustees, fees, sdk_pool_handle):
    _, rep = send_set_fees(looper, trustees, fees, sdk_pool_handle)[0]
    return rep['result']


def get_fees_request(sender_did):
    op = {
        TXN_TYPE: GET_FEES,
    }
    request = sdk_gen_request(op, identifier=sender_did)
    return request


def send_get_fees(looper, sdk_wallet_client, sdk_pool_handle):
    _, sender_did = sdk_wallet_client
    request = get_fees_request(sender_did)
    req_resp_json = sdk_sign_and_submit_req_obj(looper, sdk_pool_handle,
                                                sdk_wallet_client, request)
    _, reply = sdk_get_and_check_replies(looper, [req_resp_json, ])[0]
    return reply['result']


def get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle):
    res = send_get_fees(looper, sdk_wallet_client, sdk_pool_handle)
    return res[FEES]


def check_fee_req_handler_in_memory_map_updated(nodes, fees):
    for node in nodes:
        assert node.get_req_handler(txn_type=FEE).fees == fees


def gen_nym_req_for_fees(looper, creators_wallet, seed=None):
    name = randomString(6)
    seed = seed or randomString(32)
    nym_request, new_did = looper.loop.run_until_complete(
        prepare_nym_request(creators_wallet, seed,
                            name, None))

    signed_req = sdk_sign_request_objects(looper, creators_wallet,
                                           [sdk_json_to_request_object(
                                               json.loads(nym_request))])[0]

    req_obj = sdk_json_to_request_object(json.loads(signed_req))
    if req_obj.signatures is None:
        req_obj.signatures = {}
    req_obj.signatures[req_obj._identifier] = req_obj.signature
    req_obj._identifier = None
    req_obj.signature = None
    return req_obj
