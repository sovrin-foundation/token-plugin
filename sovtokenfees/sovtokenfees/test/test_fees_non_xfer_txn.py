import json
import pytest

from plenum.common.constants import TXN_TYPE, DOMAIN_LEDGER_ID
from plenum.common.exceptions import RequestRejectedException, RequestNackedException
from plenum.common.txn_util import get_seq_no
from plenum.common.types import f
from sovtoken.test.helper import send_get_utxo, do_public_minting
from sovtokenfees.constants import FEES, REF
from sovtokenfees.test.helper import gen_nym_req_for_fees
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import INPUTS, OUTPUTS
from sovtoken.util import update_token_wallet_with_result
from plenum.test.helper import sdk_send_and_check
from sovtokenfees.test.test_set_get_fees import fees_set


@pytest.fixture(scope="module")
def fees_paid(tokens_distributed, looper, sdk_wallet_steward,  # noqa
              sdk_pool_handle, fees_set, user1_address, user1_token_wallet):

    # =============
    # Declaration of helper functions.
    # =============

    def add_fees_request(request, wallet, address):
        fee_amount = fees_set[FEES][request.operation[TXN_TYPE]]
        request_with_fees = wallet.add_fees_to_request(
            request, fee_amount=fee_amount, address=address
        )
        return request_with_fees

    def get_address_utxos(wallet, address):
        return wallet.addresses[address].all_utxos

    def send_request_object_and_check(request):
        sent_requests = sdk_send_and_check(
            [json.dumps(req.__dict__)],
            looper,
            None,
            sdk_pool_handle,
            5
        )
        return sent_requests[0][1]

    # =============
    # Build nym request with fees.
    # =============

    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    req = add_fees_request(req, user1_token_wallet, user1_address)
    utxos_before = get_address_utxos(user1_token_wallet, user1_address)

    # =============
    # Send nym request with fees.
    # =============

    result = send_request_object_and_check(req)['result']
    update_token_wallet_with_result(user1_token_wallet, result)
    utxos_after = get_address_utxos(user1_token_wallet, user1_address)

    assert utxos_after != utxos_before
    return result


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
    req = user1_token_wallet.add_fees_to_request(
        req, fee_amount=fee_amount, address=user1_address
    )

    fees = getattr(req, f.FEES.nm)
    # reverse the signatures to make them incorrect
    fees[2] = [sig[::-1] for sig in fees[2]]
    setattr(req, f.FEES.nm, fees)
    req_json = json.dumps(req.__dict__)

    with pytest.raises(RequestNackedException):
        sdk_send_and_check([req_json], looper, None, sdk_pool_handle, 5)


def test_invalid_fees_valid_payload(tokens_distributed, looper, sdk_wallet_steward,  # noqa
                                    sdk_pool_handle, fees_set, user1_address,
                                    user1_token_wallet, seller_token_wallet,
                                    seller_address):
    """
    The fee amount is correct but the one of the 2 payers does not have enough
    tokens to pay the sovtokenfees, though the payload is a valid txn.
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
    updated_fees = [existing_fees[0] + fees[0], existing_fees[1], existing_fees[2] + fees[2]]
    setattr(req, f.FEES.nm, updated_fees)
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


def test_valid_txn_with_fees(fees_paid, nodeSetWithIntegratedTokenPlugin, looper,
                             user1_address, sdk_wallet_client, sdk_pool_handle):
    """
    Provide sufficient sovtokenfees for transaction with correct signatures and payload
    """
    for node in nodeSetWithIntegratedTokenPlugin:
        token_ledger = node.getLedger(TOKEN_LEDGER_ID)
        assert len(token_ledger.uncommittedTxns) == 0
        fee_txn = token_ledger.getBySeqNo(token_ledger.size)
        assert fee_txn[INPUTS] == fees_paid[FEES][INPUTS]
        assert fee_txn[OUTPUTS] == fees_paid[FEES][OUTPUTS]
        assert fee_txn[REF] == '{}:{}'.format(DOMAIN_LEDGER_ID,
                                              get_seq_no(fees_paid))
    res = send_get_utxo(looper, user1_address, sdk_wallet_client,
                        sdk_pool_handle)
    assert user1_address in res[OUTPUTS][0]
    assert get_seq_no(fee_txn) in res[OUTPUTS][0]
    assert fees_paid[FEES][OUTPUTS][0][-1] in res[OUTPUTS][0]


def test_fees_utxo_reuse(fees_paid, user1_token_wallet, sdk_wallet_steward,
                         looper, sdk_pool_handle, fees_set):
    """
    Check that utxo used in sovtokenfees cannot be reused
    """
    fees_req = fees_paid
    req = gen_nym_req_for_fees(looper, sdk_wallet_steward)
    paying_utxo = fees_req[FEES][INPUTS][0]
    fees = user1_token_wallet.get_fees([paying_utxo, ],
                                       fees_req[FEES][OUTPUTS])
    req.__setattr__(f.FEES.nm, fees)
    with pytest.raises(RequestRejectedException):
        sdk_send_and_check([json.dumps(req.__dict__)], looper, None,
                           sdk_pool_handle, 5)


def test_mint_after_paying_fees(fees_paid, looper, nodeSetWithIntegratedTokenPlugin,
                             trustee_wallets, SF_address, seller_address,
                             sdk_pool_handle):
    # Try another minting after doing some txns with fees
    total_mint = 100
    sf_master_gets = 60
    do_public_minting(looper, trustee_wallets, sdk_pool_handle, total_mint,
                      sf_master_gets, SF_address, seller_address)
