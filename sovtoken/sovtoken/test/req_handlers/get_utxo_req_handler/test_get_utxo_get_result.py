import pytest
from sovtoken.constants import OUTPUTS, ADDRESS
from sovtoken.request_handlers.token_utils import TokenStaticHelper
from sovtoken.test.helper import libsovtoken_address_to_address

from plenum.common.constants import STATE_PROOF


@pytest.fixture(scope="module", autouse=True)
def add_utxo(payment_address, get_utxo_handler):
    get_utxo_handler.state.set(TokenStaticHelper.create_state_key(libsovtoken_address_to_address(payment_address), 1), "3".encode())


def test_get_utxo_request_has_utxos(get_utxo_request, get_utxo_handler, payment_address, add_utxo):
    result = get_utxo_handler.get_result(get_utxo_request)
    assert result[STATE_PROOF]
    assert result[OUTPUTS]
    assert len(result[OUTPUTS]) == 1
    assert result[OUTPUTS][0].address == libsovtoken_address_to_address(payment_address)
    assert result[OUTPUTS][0].amount == 3
    assert result[OUTPUTS][0].seqNo == 1


def test_get_utxo_request_no_utxos(get_utxo_request, get_utxo_handler, payment_address_2, add_utxo):
    get_utxo_request.operation[ADDRESS] = libsovtoken_address_to_address(payment_address_2)
    result = get_utxo_handler.get_result(get_utxo_request)
    assert result[STATE_PROOF]
    assert len(result[OUTPUTS]) == 0
