from sovtoken.constants import OUTPUTS, UTXO_LIMIT
from sovtoken.test.helper import libsovtoken_address_to_address
from sovtoken.test.req_handlers.get_utxo_req_handler.conftest import FROM_SHIFT

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


def test_get_utxo_request_has_utxos(get_utxo_request, get_utxo_handler, payment_address, insert_over_thousand_utxos):
    result = get_utxo_handler.get_result(get_utxo_request)
    assert result[STATE_PROOF]
    assert result[OUTPUTS]
    assert len(result[OUTPUTS]) == UTXO_LIMIT
    for i in range(UTXO_LIMIT):
        assert result[OUTPUTS][i].address == libsovtoken_address_to_address(payment_address)
        assert result[OUTPUTS][i].seqNo == i
        assert result[OUTPUTS][i].amount == i


def test_get_utxo_request_has_utxos_with_from(get_utxo_request_with_from, get_utxo_handler, payment_address, insert_over_thousand_utxos):
    result = get_utxo_handler.get_result(get_utxo_request_with_from)
    assert result[STATE_PROOF]
    assert result[OUTPUTS]
    assert len(result[OUTPUTS]) == UTXO_LIMIT
    for i in range(FROM_SHIFT, FROM_SHIFT+UTXO_LIMIT):
        assert result[OUTPUTS][i-FROM_SHIFT].address == libsovtoken_address_to_address(payment_address)
        assert result[OUTPUTS][i-FROM_SHIFT].seqNo == i
        assert result[OUTPUTS][i-FROM_SHIFT].amount == i
