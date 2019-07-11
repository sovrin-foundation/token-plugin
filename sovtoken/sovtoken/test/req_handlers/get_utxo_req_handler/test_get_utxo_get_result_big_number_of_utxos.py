from sovtoken.constants import OUTPUTS, UTXO_LIMIT, FROM_SEQNO
from sovtoken.test.helper import libsovtoken_address_to_address

from plenum.common.constants import STATE_PROOF


def test_get_utxo_request_has_utxos(get_utxo_request, get_utxo_handler, payment_address, insert_over_thousand_utxos):
    result = get_utxo_handler.get_result(get_utxo_request)
    assert result[STATE_PROOF]
    assert result[OUTPUTS]
    assert len(result[OUTPUTS]) == UTXO_LIMIT
    for i in range(UTXO_LIMIT):
        assert result[OUTPUTS][i].address == libsovtoken_address_to_address(payment_address)
        assert result[OUTPUTS][i].seqNo == i
        assert result[OUTPUTS][i].amount == i

FROM_SHIFT = 200

def test_get_utxo_request_has_utxos_with_from(get_utxo_request, get_utxo_handler, payment_address, insert_over_thousand_utxos):
    get_utxo_request.operation[FROM_SEQNO] = FROM_SHIFT
    result = get_utxo_handler.get_result(get_utxo_request)
    assert result[STATE_PROOF]
    assert result[OUTPUTS]
    assert len(result[OUTPUTS]) == UTXO_LIMIT
    for i in range(FROM_SHIFT, FROM_SHIFT+UTXO_LIMIT):
        assert result[OUTPUTS][i-FROM_SHIFT].address == libsovtoken_address_to_address(payment_address)
        assert result[OUTPUTS][i-FROM_SHIFT].seqNo == i
        assert result[OUTPUTS][i-FROM_SHIFT].amount == i


def test_get_utxo_request_has_utxos_with_from_bigger_than_utxos(get_utxo_request, get_utxo_handler, payment_address, insert_over_thousand_utxos):
    get_utxo_request.operation[FROM_SEQNO] = 13000
    result = get_utxo_handler.get_result(get_utxo_request)
    assert result[STATE_PROOF]
    assert result[OUTPUTS] == []


def test_get_utxo_request_has_utxos_with_from_between_the_numbers(get_utxo_request, get_utxo_handler, payment_address,
                                                                  insert_over_thousand_utxos, insert_utxos_after_gap):
    gap = insert_utxos_after_gap
    # there is a gap between 1200 and 1300 seqno's for this payment address
    get_utxo_request.operation[FROM_SEQNO] = gap - 50
    result = get_utxo_handler.get_result(get_utxo_request)
    # 2300 utxos is too many for state proof, not checking it
    assert result[OUTPUTS]
    assert len(result[OUTPUTS]) == UTXO_LIMIT
    for i in range(gap, gap+UTXO_LIMIT):
        assert result[OUTPUTS][i-gap].address == libsovtoken_address_to_address(payment_address)
        assert result[OUTPUTS][i-gap].seqNo == i
        assert result[OUTPUTS][i-gap].amount == i
