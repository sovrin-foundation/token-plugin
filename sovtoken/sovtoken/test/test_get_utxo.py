import pytest

from plenum.common.exceptions import RequestNackedException
from plenum.common.txn_util import get_seq_no, get_payload_data
from sovtoken.constants import OUTPUTS, ADDRESS
from sovtoken.test.wallet import Address


def test_empty_address(helpers):
    address = Address()
    address.address = ''
    with pytest.raises(RequestNackedException):
        helpers.general.do_get_utxo(address)


def test_invalid_address(helpers):
    # Replace three characters in address
    address = Address()
    address.address = address.address[:3] + "000" + address.address[6:]
    with pytest.raises(RequestNackedException):
        helpers.general.do_get_utxo(address)


def test_address_no_utxos(helpers):
    response = helpers.general.do_get_utxo(Address())
    assert response[OUTPUTS] == []


def test_address_utxos(helpers):
    """ Mint tokens and get the utxos for an address """

    address = Address()
    outputs = [[address, 1000]]
    mint_result = helpers.general.do_mint(outputs)

    mint_seq_no = get_seq_no(mint_result)
    get_utxo_result = helpers.general.do_get_utxo(address)

    assert get_utxo_result[OUTPUTS] == [[address.address, mint_seq_no, 1000]]


# We can't handle multiple addresses at the moment because it requires a more
# complicated state proof. So this test has been changed to show that multiple
# addresses are not accepted.
def test_get_multiple_addresses(helpers):
    addresses = [Address(), Address()]
    
    # Create a request with a single address and then replace it to check for
    # multiple addresses.
    request = helpers.request.get_utxo(addresses[0])
    request.operation[ADDRESS] = [address.address for address in addresses]

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_get_utxo_utxos_in_order(helpers):
    """
    In response of GET_UTXO make sure all UTXOs are ordered in the same way; ascending order of seq_no
    """

    address_1 = Address()
    address_2 = Address()
    total = 100
    outputs = [[address_1, total]]
    mint_result = helpers.general.do_mint(outputs)

    seq_no = get_seq_no(mint_result)

    remaining = total
    for _ in range(10):
        inputs = [
            [address_1, seq_no],
        ]
        outputs = [
            [address_2, 1],
            [address_1, remaining - 1]
        ]
        request = helpers.request.transfer(inputs, outputs)
        response = helpers.sdk.send_and_check_request_objects([request])
        result = helpers.sdk.get_first_result(response)
        seq_no = get_seq_no(result)
        remaining -= 1

    request = helpers.request.get_utxo(address_1)
    responses = helpers.sdk.send_and_check_request_objects([request])
    for response in responses:
        result = response[1]['result']
        seq_nos = []
        for output in result[OUTPUTS]:
            seq_nos.append(output[1])

        assert seq_nos == sorted(seq_nos)
