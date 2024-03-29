import json
import math
import pytest

from base58 import b58encode_check

from plenum.common.constants import TXN_TYPE, DOMAIN_LEDGER_ID, NYM, DATA
from plenum.common.exceptions import RequestRejectedException, RequestNackedException
from plenum.common.txn_util import get_seq_no, get_payload_data, get_txn_time
from plenum.common.types import f
from plenum.common.util import randomString

from sovtoken.test.wallet import Address
from sovtokenfees.constants import FEES, REF
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import INPUTS, OUTPUTS, AMOUNT, ADDRESS, SEQNO, PAYMENT_ADDRESS
from sovtokenfees.test.constants import NYM_FEES_ALIAS, txn_type_to_alias
from sovtokenfees.test.helper import pay_fees, add_fees_request_with_address, pay_fees_inner


@pytest.fixture()
def address_main_inner(helpers):
    return helpers.inner.wallet.create_address()


@pytest.fixture()
def fees_paid(
    helpers,
    fees_set,
    address_main,
    mint_tokens
):
    return pay_fees(helpers, fees_set, address_main)


@pytest.fixture()
def fees_paid_manually(
    helpers,
    fees_set,
    address_main_inner,
    mint_tokens_inner
):
    return pay_fees_inner(helpers, fees_set, address_main_inner)


def test_invalid_fees_numeric(helpers, mint_tokens):

    address_main = helpers.inner.wallet.create_address()

    """
    Testing fees outputs with an invalid numeric type
    """
    def _test_invalid_fees(amount, fees=False):
        if fees:
            fees_amount = {
                NYM_FEES_ALIAS: fees
            }
            helpers.general.do_set_fees(fees_amount)

        seq_no = get_seq_no(mint_tokens)
        inputs = [
            {ADDRESS: address_main, SEQNO: seq_no}
        ]
        outputs = [
            {ADDRESS: address_main, AMOUNT: amount}
        ]

        request = helpers.request.nym()

        request = helpers.inner.request.add_fees_specific(
            request,
            inputs,
            outputs
        )

        with pytest.raises(RequestNackedException):
            helpers.sdk.send_and_check_request_objects([request])

    _test_invalid_fees(-1, fees=1001)
    _test_invalid_fees(0, fees=1000)
    _test_invalid_fees(4.5, fees=None)
    _test_invalid_fees(None, fees=None)


def test_zero_fees(
    helpers,
    address_main,
    mint_tokens
):
    """
    The fee amount is zero
    """

    helpers.general.do_set_fees({NYM_FEES_ALIAS: 0})

    req = helpers.request.nym()
    utxos = helpers.general.get_utxo_addresses([address_main])[0]
    request = helpers.request.add_fees(
        req,
        utxos,
        0,
        change_address=address_main
    )[0]

    helpers.sdk.sdk_send_and_check([request])


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
    txn_type = req.operation[TXN_TYPE]
    fee_amount = fees_set[FEES][txn_type_to_alias[txn_type]] - 1
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
    txn_type = req.operation[TXN_TYPE]
    fee_amount = fees_set[FEES][txn_type_to_alias[txn_type]] + 1
    utxos = helpers.general.get_utxo_addresses([address_main])[0]
    helpers.request.add_fees(
        req,
        utxos,
        fee_amount,
        change_address=address_main
    )

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([req])


def test_invalid_address(helpers, address_main_inner, mint_tokens_inner, fees, fees_set):
    """
    Fees with invalid address.
    """

    def _update_char(s, index, func):
        return s[:index] + func(s[index]) + s[index + 1:]

    def _test_invalid_address(address):
        utxos = helpers.inner.general.get_utxo_addresses([address_main_inner])[0]
        request = helpers.request.nym()
        request = helpers.inner.request.add_fees(
            request,
            utxos,
            fees[NYM_FEES_ALIAS],
            change_address=[address]
        )

        with pytest.raises(RequestNackedException):
            helpers.sdk.send_and_check_request_objects([request])

    invalid_address_length = b58encode_check(randomString(33).encode()).decode()
    invalid_address_character = _update_char(address_main_inner, 2, lambda _: '!')
    invalid_address_checksum = _update_char(
        address_main_inner,
        2,
        lambda c: 'B' if c == 'A' else 'A'
    )

    _test_invalid_address(invalid_address_length)
    _test_invalid_address(invalid_address_character)
    _test_invalid_address(invalid_address_checksum)


def test_fees_too_many_outputs(
    helpers,
    fees_set,
    address_main,
    xfer_addresses,
    mint_tokens,
):
    """
    More than one output address
    """
    req = helpers.request.nym()
    txn_type = req.operation[TXN_TYPE]
    fee_amount = fees_set[FEES][txn_type_to_alias[txn_type]]
    utxos = helpers.general.get_utxo_addresses([address_main])[0]
    req = helpers.request.add_fees(
        req,
        utxos,
        fee_amount,
        change_address=[address_main, xfer_addresses[0]]
    )[0]
    with pytest.raises(RequestNackedException):
        helpers.sdk.sdk_send_and_check([req])


def test_fees_output_with_zero_tokens(
    helpers,
    address_main,
    fees,
    fees_set,
):
    """
    A fee output can't be set to zero tokens.
    """
    outputs = [{ADDRESS: address_main, AMOUNT: int(fees[NYM_FEES_ALIAS])}]
    helpers.general.do_mint(outputs)

    empty_address = helpers.wallet.create_address()
    inputs = helpers.general.get_utxo_addresses([address_main])[0]
    outputs = [{ADDRESS: empty_address, AMOUNT: 0}]

    request = helpers.request.nym()
    request = helpers.request.add_fees_specific(request, inputs, outputs)[0]

    with pytest.raises(RequestNackedException):
        helpers.sdk.sdk_send_and_check([request])


def test_no_fees_when_required(
    helpers,
    fees_set,
    address_main,
):
    """
    No fees, both null fee field and no fee field
    """
    req = helpers.request.nym()
    txn_type = req.operation[TXN_TYPE]
    fee_amount = fees_set[FEES][txn_type_to_alias[txn_type]]
    assert(fee_amount != 0)

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([req])

    helpers.general.get_utxo_addresses([address_main])[0]

    setattr(req, FEES, None)

    with pytest.raises(RequestNackedException):
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


def test_fees_insufficient_sig(
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
    # set only one signature instead of two
    fees[2] = []
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
    sig = getattr(request, f.SIG.nm)
    # Reverse the signature of NYM txn sender, making it invalid
    sig = sig[::-1]
    setattr(request, f.SIG.nm, sig)
    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_fees_extra_field(helpers, address_main, mint_tokens, fees_set):
    """
    The fees section has an extra field.
    """
    request = helpers.request.nym()
    request = add_fees_request_with_address(
        helpers,
        fees_set,
        request,
        address_main
    )

    fees = request.fees
    fees.append([])
    request.fees = fees
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
        helpers.sdk.send_and_check_request_objects([req], sdk_wallet_client)


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
    print(fee_payload_from_resp)

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
    expected_amount = fee_payload_from_resp[OUTPUTS][0][AMOUNT]
    assert last_utxo[PAYMENT_ADDRESS] == address_main
    assert last_utxo[AMOUNT] == expected_amount


def test_get_fees_txn(helpers, fees_paid, nodeSetWithIntegratedTokenPlugin):
    seq_no = get_seq_no(fees_paid[FEES])
    request = helpers.request.get_txn(str(TOKEN_LEDGER_ID), seq_no)
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
    fees_paid_manually,
    fees_set,
    address_main_inner
):
    """
    Check that utxo used in sovtokenfees cannot be reused
    """
    nym_fees_data = get_payload_data(fees_paid_manually[FEES])
    inputs = nym_fees_data[INPUTS]
    outputs = nym_fees_data[OUTPUTS]
    fees_set[FEES][NYM_FEES_ALIAS]

    req = helpers.request.nym()
    fee_sigs = helpers.inner.request.fees_signatures(
        inputs,
        outputs,
        req.payload_digest
    )
    fees = [inputs, outputs, fee_sigs]
    setattr(req, FEES, fees)

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([req])


def test_append_fees_to_different_transaction(helpers, address_main, mint_tokens):
    fees = {NYM_FEES_ALIAS: 1}
    helpers.general.do_set_fees(fees)
    utxos = helpers.general.get_utxo_addresses([address_main])[0]

    request = helpers.request.nym()
    request = helpers.request.add_fees(
        request,
        utxos,
        fees[NYM_FEES_ALIAS],
        change_address=address_main
    )[0]

    new_request = helpers.request.nym()

    request = json.loads(request)
    new_request = new_request.as_dict

    new_request[FEES] = request[FEES]

    with pytest.raises(RequestNackedException):
        helpers.sdk.sdk_send_and_check([json.dumps(new_request)])
