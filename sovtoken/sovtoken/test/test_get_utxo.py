import pytest

from plenum.common.exceptions import (RequestNackedException,
                                      RequestRejectedException)
from plenum.common.txn_util import get_seq_no
from sovtoken.constants import OUTPUTS, ADDRESS
from sovtoken.wallet import Address


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
    """ Mint tokens and get the utxos for multiple addresses """

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
