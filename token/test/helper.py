import json

from plenum.common.constants import TXN_TYPE
from plenum.server.plugin.token.src.constants import MINT_PUBLIC, OUTPUTS, XFER_PUBLIC, \
    EXTRA, TOKEN_LEDGER_ID, GET_UTXO, ADDRESSES
from plenum.test.helper import sdk_send_signed_requests, \
    sdk_get_and_check_replies, sdk_gen_request, sdk_sign_and_submit_req_obj


def public_mint_request(trustees, outputs):
    signatures = {}
    op = {
        TXN_TYPE: MINT_PUBLIC,
        OUTPUTS: outputs,
    }
    first_trustee = trustees[0]
    request = first_trustee.sign_using_multi_sig(
        op, identifier=first_trustee.defaultId)
    for wallet in trustees[1:]:
        signatures[wallet.defaultId] = wallet.do_multi_sig_on_req(
            request, identifier=wallet.defaultId)
    return request


def send_public_mint(looper, trustees, outputs, sdk_pool_handle):
    request = public_mint_request(trustees, outputs)
    request = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(request.as_dict), ])
    return sdk_get_and_check_replies(looper, request)


def do_public_minting(looper, trustees, sdk_pool_handle, total_mint,
                      sf_master_share, sf_address, seller_address):
    seller_share = total_mint - sf_master_share
    outputs = [[sf_address, sf_master_share], [seller_address, seller_share]]
    _, reply = send_public_mint(looper, trustees, outputs, sdk_pool_handle)[0]
    return reply['result']


def xfer_request(inputs, outputs, extra_data=None):
    payload = {
        TXN_TYPE: XFER_PUBLIC,
        OUTPUTS: outputs,
        EXTRA: extra_data,
    }
    wallet, address, seq_no = inputs[0]
    request = wallet.sign_using_output(address, seq_no, op=payload)
    for wallet, address, seq_no in inputs[1:]:
        wallet.sign_using_output(address, seq_no, request=request)
    return request


def send_xfer(looper, inputs, outputs, sdk_pool_handle, extra_data=None):
    request = xfer_request(inputs, outputs, extra_data)
    request = sdk_send_signed_requests(sdk_pool_handle,
                                       [json.dumps(request.as_dict), ])
    _, rep = sdk_get_and_check_replies(looper, request)[0]
    return rep['result']


def check_output_val_on_all_nodes(nodes, address, amount):
    for node in nodes:
        handler = node.get_req_handler(ledger_id=TOKEN_LEDGER_ID)
        assert int(amount) in [out.value for out in
                               handler.utxo_cache.get_unspent_outputs(
                                   address, is_committed=True)]


def get_utxo_request(addresses, sender_did):
    op = {
        TXN_TYPE: GET_UTXO,
        ADDRESSES: addresses,
    }
    request = sdk_gen_request(op, identifier=sender_did)
    return request


def send_get_utxo(looper, addresses, sdk_wallet_client, sdk_pool_handle):
    if isinstance(addresses, str):
        addresses = [addresses]

    _, sender_did = sdk_wallet_client
    request = get_utxo_request(addresses, sender_did)
    req_resp_json = sdk_sign_and_submit_req_obj(looper, sdk_pool_handle,
                                           sdk_wallet_client, request)
    _, reply = sdk_get_and_check_replies(looper, [req_resp_json, ])[0]
    return reply['result']


def inputs_outputs(*input_token_wallets, output_addr, change_addr=None,
                   change_amount=None):
    inputs = []
    out_amount = 0
    for tw in input_token_wallets:
        addr, vals = next(iter(tw.get_all_wallet_utxos().items()))
        inputs.append([tw, addr.address, vals[0][0]])
        out_amount += vals[0][1]

    if change_amount is not None:
        assert change_amount <= out_amount
        out_amount -= change_amount

    outputs = [[output_addr, out_amount], ]
    if change_addr:
        outputs.append([change_addr, change_amount])
    return inputs, outputs
