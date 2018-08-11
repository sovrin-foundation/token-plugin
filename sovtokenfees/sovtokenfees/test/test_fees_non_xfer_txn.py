import json
import pytest

from plenum.common.constants import TXN_TYPE, DOMAIN_LEDGER_ID, NYM, DATA
from plenum.common.exceptions import RequestRejectedException, RequestNackedException
from plenum.common.txn_util import get_seq_no, get_payload_data, get_txn_time
from plenum.common.types import f
from plenum.test.pool_transactions.helper import sdk_build_get_txn_request
from sovtoken.test.wallet import Address
from sovtokenfees.constants import FEES, REF
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import INPUTS, OUTPUTS


def add_fees_request_with_address(helpers, fees_set, request, address):
    utxos = helpers.general.get_utxo_addresses([address])[0]
    fee_amount = fees_set[FEES][request.operation[TXN_TYPE]]
    helpers.request.add_fees(
        request,
        utxos,
        fee_amount,
        change_address=address
    )
    return request


@pytest.fixture(scope="module")
def address_main():
    return Address()


@pytest.fixture(scope="module")
def mint_tokens(helpers, address_main):
    return helpers.general.do_mint([[address_main, 1000]])


def pay_fees(helpers, fees_set, address_main, mint_tokens):
    request = helpers.request.nym()

    request = add_fees_request_with_address(
        helpers,
        fees_set,
        request,
        address_main
    )

    responses = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(responses)
    return result


@pytest.fixture()
def fees_paid(
    helpers,
    fees_set,
    address_main,
    mint_tokens
):
    return pay_fees(helpers, fees_set, address_main, mint_tokens)


def test_insufficient_fees(
    helpers,
    address_main,
    mint_tokens,
    fees_set,
):
    """
    The fee amount is less than required
    """
    req = helpers.request.nym()
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]] - 1
    utxos = helpers.general.get_utxo_addresses([address_main])[0]
    helpers.request.add_fees(
        req,
        utxos,
        fee_amount,
        change_address=address_main
    )

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([req])


def test_fees_larger(
    helpers,
    fees_set,
    address_main,
    mint_tokens,
):
    """
    The fee amount is more than required
    """
    req = helpers.request.nym()
    fee_amount = fees_set[FEES][req.operation[TXN_TYPE]] + 1
    utxos = helpers.general.get_utxo_addresses([address_main])[0]
    helpers.request.add_fees(
        req,
        utxos,
        fee_amount,
        change_address=address_main
    )

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([req])


def test_fees_incorrect_sig(
    helpers,
    fees_set,
    address_main,
    mint_tokens
):
    """
    The fee amount is correct but signature over the fee is incorrect.
    """
    request = helpers.request.nym()
    request = add_fees_request_with_address(
        helpers,
        fees_set,
        request,
        address_main
    )
    fees = getattr(request, FEES)
    # reverse the signatures to make them incorrect
    fees[2] = [sig[::-1] for sig in fees[2]]
    setattr(request, FEES, fees)

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_valid_fees_invalid_payload_sig(
    helpers,
    fees_set,
    address_main,
    mint_tokens
):
    """
    The fee part of the txn is valid but the payload has invalid signature
    """
    request = helpers.request.nym()
    request = add_fees_request_with_address(
        helpers,
        fees_set,
        request,
        address_main
    )
    sigs = getattr(request, f.SIGS.nm)
    # Reverse the signature of NYM txn sender, making it invalid
    first_sig_did = next(iter(sigs.keys()))
    sigs[first_sig_did] = sigs[first_sig_did][::-1]
    setattr(request, f.SIGS.nm, sigs)
    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_valid_fees_invalid_payload(
    helpers,
    fees_set,
    mint_tokens,
    address_main,
    sdk_wallet_client
):
    """
    The fee part of the txn is valid but the payload fails dynamic validation
    (unauthorised request)
    """
    req = helpers.request.nym(sdk_wallet=sdk_wallet_client)
    req = add_fees_request_with_address(
        helpers,
        fees_set,
        req,
        address_main
    )

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([req])


def test_valid_txn_with_fees(
    helpers,
    fees_paid,
    nodeSetWithIntegratedTokenPlugin,
    address_main
):
    """
    Provide sufficient sovtokenfees for transaction with correct signatures and payload
    """
    fee_payload_from_resp = get_payload_data(fees_paid[FEES])

    for node in nodeSetWithIntegratedTokenPlugin:
        token_ledger = node.getLedger(TOKEN_LEDGER_ID)
        assert len(token_ledger.uncommittedTxns) == 0

        fee_txn = token_ledger.getBySeqNo(token_ledger.size)
        fee_payload_from_ledger = get_payload_data(fee_txn)
        expected_ref = '{}:{}'.format(DOMAIN_LEDGER_ID, get_seq_no(fees_paid))

        assert fee_payload_from_ledger[INPUTS] == fee_payload_from_resp[INPUTS]
        assert fee_payload_from_ledger[OUTPUTS] == fee_payload_from_resp[OUTPUTS]
        assert fee_payload_from_ledger[REF] == expected_ref

    utxos = helpers.general.get_utxo_addresses([address_main])[0]
    last_utxo = utxos[-1]
    expected_amount = fee_payload_from_resp[OUTPUTS][0][-1]
    assert last_utxo == [address_main, get_seq_no(fee_txn), expected_amount]


def test_get_fees_txn(helpers, fees_paid, nodeSetWithIntegratedTokenPlugin):
    seq_no = get_seq_no(fees_paid[FEES])
    request = helpers.request.get_txn(TOKEN_LEDGER_ID, seq_no)
    responses = helpers.sdk.send_and_check_request_objects([request, ])
    result = helpers.sdk.get_first_result(responses)
    data = result[DATA]
    for node in nodeSetWithIntegratedTokenPlugin:
        token_ledger = node.getLedger(TOKEN_LEDGER_ID)
        fee_txn = token_ledger.getBySeqNo(seq_no)
        assert get_payload_data(fee_txn) == get_payload_data(data)
        assert get_seq_no(fee_txn) == get_seq_no(data)
        assert get_txn_time(fee_txn) == get_txn_time(data)


def test_fees_utxo_reuse(
    helpers,
    fees_paid,
    fees_set,
    address_main
):
    """
    Check that utxo used in sovtokenfees cannot be reused
    """
    nym_fees_data = get_payload_data(fees_paid[FEES])
    inputs = nym_fees_data[INPUTS]
    outputs = nym_fees_data[OUTPUTS]
    fee_amount = fees_set[FEES][NYM]

    # Set inputs and outputs to have Address object
    inputs_addr = [[address_main, seq_no, None] for _, seq_no in inputs]
    outputs_addr = [[address_main, amount] for _, amount in outputs]

    req = helpers.request.nym()
    fee_sigs = helpers.request.fees_signatures(
        inputs_addr,
        outputs_addr,
        req.digest
    )
    fees = [inputs, outputs, fee_sigs]
    setattr(req, FEES, fees)

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([req])
