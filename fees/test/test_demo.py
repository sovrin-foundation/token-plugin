import pytest

import json
from plenum.common.constants import NYM
from plenum.server.plugin.fees.src.constants import FEES
from plenum.server.plugin.fees.src.wallet import FeeSupportedWallet
from plenum.server.plugin.fees.test.helper import send_set_fees, get_fees_from_ledger, gen_nym_req_for_fees
from plenum.server.plugin.token.src.util import update_token_wallet_with_result
from plenum.server.plugin.token.src.wallet import Address
from plenum.server.plugin.token.test.helper import send_public_mint, send_get_utxo
from plenum.test.helper import sdk_send_and_check

MINT_TOKEN_AMOUNT = 10

TXN_FEES = {
    NYM: 3
}

client_wallet = FeeSupportedWallet("RichDemoWallet")
client_address = Address()
client_wallet.add_new_address(client_address)


def mint_tokens(looper, trustee_wallets, sdk_pool_handle, address, tokens):
    outputs = [[address, tokens]]
    (_request, reply) = send_public_mint(looper, trustee_wallets, outputs, sdk_pool_handle)[0]
    return reply


def set_fees(looper, trustee_wallets, fees, sdk_pool_handle):
    (_request, reply) = send_set_fees(looper, trustee_wallets, fees, sdk_pool_handle)[0]
    return reply


def get_fees(looper, sdk_wallet_client, sdk_pool_handle):
    resp = get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle)
    return resp


def update_wallet(looper, sdk_wallet_client, sdk_pool_handle, wallet):
    wallet_addresses = list(wallet.addresses.keys())
    utxo_resp = send_get_utxo(looper, wallet_addresses, sdk_wallet_client, sdk_pool_handle)
    update_token_wallet_with_result(wallet, utxo_resp)


def get_utxo_at_wallet_address(looper, sdk_wallet_client, sdk_pool_handle, wallet, address):
    update_wallet(looper, sdk_wallet_client, sdk_pool_handle, wallet)
    return wallet.get_all_wallet_utxos()[address]


def create_nym_request(looper, sdk_wallet_steward):
    return gen_nym_req_for_fees(looper, sdk_wallet_steward)


def send_nym_request(looper, sdk_pool_handle, nym_request):
    (_request, reply) = sdk_send_and_check([json.dumps(nym_request.__dict__)], looper, None, sdk_pool_handle, 10)[0]
    return reply


def test(looper, trustee_wallets, fees, sdk_pool_handle, sdk_wallet_client, sdk_wallet_steward):


    set_reply = set_fees(looper, trustee_wallets, fees, sdk_pool_handle)
    assert set_reply['result'][FEES][NYM] == TXN_FEES[NYM]

    schema_fees = get_fees(looper, sdk_wallet_client, sdk_pool_handle)
    assert schema_fees[NYM] == TXN_FEES[NYM]

    mint_tokens_reply = mint_tokens(looper, trustee_wallets, sdk_pool_handle, client_address.address, MINT_TOKEN_AMOUNT)
    [reply_address, reply_tokens] = mint_tokens_reply['result']['outputs'][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT

    assert get_utxo_at_wallet_address(looper, sdk_wallet_client, sdk_pool_handle, client_wallet, client_address) == [(1, 10)]

    nym_request = create_nym_request(looper, sdk_wallet_steward)
    nym_request = client_wallet.add_fees_to_request(nym_request, fee_amount=schema_fees[NYM], address=client_address.address)
    nym_reply = send_nym_request(looper, sdk_pool_handle, nym_request)
    [reply_address, reply_tokens] = nym_reply['result'][FEES][1][0]
    assert reply_address == client_address.address
    assert reply_tokens == MINT_TOKEN_AMOUNT - TXN_FEES[NYM]


    # assert get_utxo_at_wallet_address(looper, sdk_wallet_client, sdk_pool_handle, client_wallet, client_address) == [(2, MINT_TOKEN_AMOUNT - TXN_FEES[NYM])]


