import pytest
from sovtokenfees.test.constants import NYM_FEES_ALIAS
from sovtokenfees.test.helper import add_fees_request_with_address

from indy_common.constants import NYM
from plenum.common.exceptions import RequestRejectedException


def send_nym_with_fees(helpers, address, change_address, fees_set, adjust_fees=0):
    (did, verkey) = helpers.wallet.create_did()
    request = helpers.request.nym(dest=did, verkey=verkey)
    request = add_fees_request_with_address(helpers, fees_set, request, address, change_address=change_address, adjust_fees=adjust_fees)
    helpers.sdk.send_and_check_request_objects([request])
    return did


def test_fees_chain(addresses, helpers, mint_tokens, fees_set, looper):
    helpers.general.do_set_fees({NYM_FEES_ALIAS: 4})
    send_nym_with_fees(helpers, addresses[0], addresses[1], fees_set)
    send_nym_with_fees(helpers, addresses[1], addresses[2], fees_set)
    send_nym_with_fees(helpers, addresses[2], addresses[3], fees_set)

    utxos = helpers.general.get_utxo_addresses(addresses[3:])

    assert utxos[0][0]["amount"] == 988


def test_fees_chain_negative(addresses, helpers, mint_tokens, fees_set, looper):
    helpers.general.do_set_fees({NYM_FEES_ALIAS: 4})
    send_nym_with_fees(helpers, addresses[0], addresses[1], fees_set)
    with pytest.raises(RequestRejectedException):
        send_nym_with_fees(helpers, addresses[1], addresses[2], fees_set, 1)
    send_nym_with_fees(helpers, addresses[1], addresses[3], fees_set)

    utxos = helpers.general.get_utxo_addresses(addresses[3:])

    assert utxos[0][0]["amount"] == 992


def test_fees_chain_positive(addresses, helpers, mint_tokens, fees_set, looper):
    helpers.general.do_set_fees({NYM_FEES_ALIAS: 4})
    send_nym_with_fees(helpers, addresses[0], addresses[1], fees_set)
    with pytest.raises(RequestRejectedException):
        send_nym_with_fees(helpers, addresses[1], addresses[2], fees_set, -1)
    send_nym_with_fees(helpers, addresses[1], addresses[3], fees_set)

    utxos = helpers.general.get_utxo_addresses(addresses[3:])

    assert utxos[0][0]["amount"] == 992
