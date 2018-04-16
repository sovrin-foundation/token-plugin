import json

import pytest

from ledger.util import F
from plenum.common.constants import TXN_TYPE, DOMAIN_LEDGER_ID
from plenum.common.exceptions import RequestRejectedException, RequestNackedException
from plenum.common.types import f
from plenum.server.plugin.fees.src.constants import FEES, REF
from plenum.server.plugin.fees.test.helper import gen_nym_req_for_fees
from plenum.server.plugin.token import TOKEN_LEDGER_ID
from plenum.server.plugin.token.src.constants import INPUTS, OUTPUTS
from plenum.test.helper import sdk_send_and_check
from plenum.server.plugin.fees.test.test_set_get_fees import fees_set


def test_insufficient_fees(tokens_distributed, looper, sdk_wallet_steward,  # noqa
                           sdk_pool_handle, fees_set, user1_address,
                           user1_token_wallet):
    """
    The fee amount is less than required
    """
    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]]
    fee_amount -= 1
    req = user1_token_wallet.add_fees_to_request(req, fee_amount=fee_amount,
                                                 address=user1_address)
    with pytest.raises(RequestRejectedException):
        sdk_send_and_check([json.dumps(req.__dict__)], looper, None,
                           sdk_pool_handle, 5)


def test_fees_incorrect_sig(tokens_distributed, looper, sdk_wallet_steward,  # noqa
                            sdk_pool_handle, fees_set, user1_address,
                            user1_token_wallet):
    """
    The fee amount is correct but signature over the fee is incorrect.
    """
    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]]
    req = user1_token_wallet.add_fees_to_request(req, fee_amount=fee_amount,
                                                 address=user1_address)
    fee_inputs = getattr(req, f.FEES.nm)[0]
    # reverse the signatures to make them incorrect
    setattr(req, f.FEES.nm, [[a, s, sig[::-1]] for a, s, sig in fee_inputs])
    with pytest.raises(RequestNackedException):
        sdk_send_and_check([json.dumps(req.__dict__)], looper, None,
                           sdk_pool_handle, 5)


def test_invalid_fees_valid_payload(tokens_distributed, looper, sdk_wallet_steward,  # noqa
                                    sdk_pool_handle, fees_set, user1_address,
                                    user1_token_wallet, seller_token_wallet,
                                    seller_address):
    """
    The fee amount is correct but the one of the 2 payers does not have enough
    tokens to pay the fees, though the payload is a valid txn.
    """
    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]]
    req = user1_token_wallet.add_fees_to_request(req, fee_amount=fee_amount,
                                                 address=user1_address)

    utxos = seller_token_wallet.get_all_address_utxos(seller_address).values()
    utxo = next(iter(utxos))[0]
    # The second payer, "seller" owns less tokens
    assert utxo[1] < fee_amount
    existing_fees = getattr(req, f.FEES.nm)
    fees = seller_token_wallet.get_fees([[seller_address, utxo[0]]],
                                        existing_fees[1])
    updated_fees = [existing_fees[0] + fees[0], existing_fees[1]]
    setattr(req, f.FEES.nm, updated_fees)
    # for addr, sig in sigs.items():
    #     req.add_signature(addr, sig)
    with pytest.raises(RequestRejectedException):
        sdk_send_and_check([json.dumps(req.__dict__)], looper, None,
                           sdk_pool_handle, 5)


def test_valid_fees_invalid_payload_sig(tokens_distributed, looper, sdk_wallet_steward,  # noqa
                                        sdk_pool_handle, fees_set,
                                        user1_address, user1_token_wallet):
    """
    The fee part of the txn is valid but the payload has invalid signature
    """
    _, stw_did = sdk_wallet_steward
    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]]
    req = user1_token_wallet.add_fees_to_request(req, fee_amount=fee_amount,
                                                 address=user1_address)
    sigs = getattr(req, f.SIGS.nm)
    sigs[stw_did] = sigs[stw_did][::-1]
    # Reverse the signature of NYM txn sender, making it invalid
    setattr(req, f.SIGS.nm, sigs)
    with pytest.raises(RequestNackedException):
        sdk_send_and_check([json.dumps(req.__dict__)], looper, None,
                           sdk_pool_handle, 5)


def test_valid_fees_invalid_payload(tokens_distributed, looper, sdk_wallet_client,  # noqa
                                    sdk_pool_handle, fees_set,
                                    user1_address, user1_token_wallet):
    """
    The fee part of the txn is valid but the payload fails dynamic validation
    (unauthorised request)
    """
    req = gen_nym_req_for_fees(looper, sdk_wallet_client)
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]]
    req = user1_token_wallet.add_fees_to_request(req, fee_amount=fee_amount,
                                                 address=user1_address)
    with pytest.raises(RequestRejectedException):
        sdk_send_and_check([json.dumps(req.__dict__)], looper, None,
                           sdk_pool_handle, 5)


@pytest.fixture(scope="module")
def fees_paid(tokens_distributed, looper, sdk_wallet_steward,  # noqa
              sdk_pool_handle, fees_set, user1_address, user1_token_wallet):
    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]]
    req = user1_token_wallet.add_fees_to_request(req, fee_amount=fee_amount,
                                                 address=user1_address)
    res = sdk_send_and_check([json.dumps(req.__dict__)], looper, None,
                             sdk_pool_handle, 5)[0][1]['result']
    return res


def test_valid_txn_with_fees(fees_paid, nodeSetWithIntegratedTokenPlugin):
    """
    Provide sufficient fees for transaction with correct signatures and payload
    """
    for node in nodeSetWithIntegratedTokenPlugin:
        token_ledger = node.getLedger(TOKEN_LEDGER_ID)
        assert len(token_ledger.uncommittedTxns) == 0
        fee_txn = token_ledger.getBySeqNo(token_ledger.size)
        assert fee_txn[INPUTS] == fees_paid[FEES][0]
        assert fee_txn[OUTPUTS] == fees_paid[FEES][1]
        assert fee_txn[REF] == '{}:{}'.format(DOMAIN_LEDGER_ID,
                                              fees_paid[F.seqNo.name])


def test_fees_utxo_reuse(fees_paid, user1_token_wallet, sdk_wallet_steward,
                         looper, sdk_pool_handle, fees_set):
    """
    Check that utxo used in fees cannot be reused
    """
    fees_req = fees_paid
    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]]
    paying_utxo = fees_req[FEES][0][0][:2]
    req = user1_token_wallet.add_fees_to_request(req, paying_utxo=paying_utxo,
                                                 fee_amount=fee_amount)
    with pytest.raises(RequestRejectedException):
        sdk_send_and_check([json.dumps(req.__dict__)], looper, None,
                           sdk_pool_handle, 5)
