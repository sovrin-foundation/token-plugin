import json

from sovtokenfees.constants import FEES

from plenum.common.constants import STATE_PROOF


def test_get_fees_handler_get_result(get_fees_handler, get_fees_request):
    response = get_fees_handler.get_result(get_fees_request)
    assert response[STATE_PROOF]
    assert not response[FEES]
