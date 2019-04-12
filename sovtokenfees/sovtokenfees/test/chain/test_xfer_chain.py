import pytest
from sovtoken.constants import ADDRESS, AMOUNT, SEQNO

from plenum.common.exceptions import RequestRejectedException


def send_transfer_request(helpers, addresses, amount, adjust_change=0):
    [address_giver, address_receiver] = addresses

    utxos = helpers.general.get_utxo_addresses([address_giver])

    utxos = helpers.request.find_utxos_can_pay(utxos[0], amount)
    inputs = [{ADDRESS: utxo["address"], SEQNO: utxo["seqNo"]} for utxo in utxos]
    change = sum([utxo["amount"] for utxo in utxos]) - amount
    outputs = [
        {ADDRESS: address_receiver, AMOUNT: amount},
        {ADDRESS: address_giver, AMOUNT: change + adjust_change},
    ]
    result = helpers.general.do_transfer(inputs, outputs)

    return result


def test_xfer_chain(mint_tokens, helpers, addresses):
    send_transfer_request(helpers, addresses[0:2], 100)
    send_transfer_request(helpers, addresses[1:3], 90)
    send_transfer_request(helpers, addresses[2:4], 80)

    utxos = helpers.general.get_utxo_addresses(addresses)
    assert len(utxos[0]) == 1
    assert utxos[0][0]["amount"] == 900
    assert len(utxos[1]) == 1
    assert utxos[1][0]["amount"] == 10
    assert len(utxos[2]) == 1
    assert utxos[2][0]["amount"] == 10
    assert len(utxos[3]) == 1
    assert utxos[3][0]["amount"] == 80


def test_xfer_chain_negative(mint_tokens, helpers, addresses):
    send_transfer_request(helpers, addresses[0:2], 100)
    with pytest.raises(RequestRejectedException):
        send_transfer_request(helpers, addresses[1:3], 90, 20)
    send_transfer_request(helpers, [addresses[1], addresses[3]], 80)

    utxos = helpers.general.get_utxo_addresses(addresses)
    assert len(utxos[0]) == 1
    assert utxos[0][0]["amount"] == 900
    assert len(utxos[1]) == 1
    assert utxos[1][0]["amount"] == 20
    assert len(utxos[2]) == 0
    assert len(utxos[3]) == 1
    assert utxos[3][0]["amount"] == 80
