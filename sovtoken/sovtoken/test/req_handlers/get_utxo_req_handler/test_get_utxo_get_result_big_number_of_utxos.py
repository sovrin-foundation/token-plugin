from sovtoken.constants import OUTPUTS

from plenum.common.constants import STATE_PROOF


def test_get_utxo_request_has_utxos(get_utxo_request, get_utxo_handler, payment_address, insert_over_thousand_utxos):
    result = get_utxo_handler.get_result(get_utxo_request)
    assert result[STATE_PROOF]
    assert result[OUTPUTS]
    assert len(result[OUTPUTS]) == 1000
    for i in range(1000):
        assert result[OUTPUTS][i].address == payment_address[8:]
        assert result[OUTPUTS][i].seqNo == i
        assert result[OUTPUTS][i].amount == i
