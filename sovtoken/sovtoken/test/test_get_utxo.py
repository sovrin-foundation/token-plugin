from random import randint

import pytest

from base58 import b58encode_check

from plenum.common.exceptions import RequestNackedException
from plenum.common.txn_util import get_seq_no, get_payload_data
from plenum.common.util import randomString
from sovtoken.constants import OUTPUTS, ADDRESS

@pytest.fixture
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)

def test_empty_address(helpers):
    with pytest.raises(RequestNackedException):
        helpers.general.do_get_utxo('')


def test_invalid_address(helpers, addresses):
    """
    Get utxo with invalid address.
    """

    def _update_char(s, index, func):
        return s[:index] + func(s[index]) + s[index + 1:]

    def _test_invalid_address(address):
        with pytest.raises(RequestNackedException):
            helpers.general.get_utxo_addresses([address])

    valid_address = addresses[0]
    invalid_address_length = b58encode_check(randomString(33).encode()).decode()
    invalid_address_character = _update_char(valid_address, 2, lambda _: '!')
    invalid_address_checksum = _update_char(
        valid_address,
        2,
        lambda c: 'B' if c == 'A' else 'A'
    )

    _test_invalid_address(invalid_address_length)
    _test_invalid_address(invalid_address_character)
    _test_invalid_address(invalid_address_checksum)


def test_address_no_utxos(helpers, addresses):
    response = helpers.general.do_get_utxo(addresses[0])
    assert response[OUTPUTS] == []


def test_address_utxos(helpers, addresses):
    """ Mint tokens and get the utxos for an address """

    address = addresses[0]
    outputs = [{"address": address, "amount": 1000}]
    mint_result = helpers.general.do_mint(outputs)

    mint_seq_no = get_seq_no(mint_result)
    get_utxo_result = helpers.general.do_get_utxo(address)

    assert get_utxo_result[OUTPUTS] == [{"address": address, "seqNo": mint_seq_no, "amount": 1000}]


# We can't handle multiple addresses at the moment because it requires a more
# complicated state proof. So this test has been changed to show that multiple
# addresses are not accepted.
def test_get_multiple_addresses(helpers, addresses):
    
    # Create a request with a single address and then replace it to check for
    # multiple addresses.
    request = helpers.request.get_utxo(addresses[0])
    request.operation[ADDRESS] = [address for address in addresses]

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_get_utxo_utxos_in_order(helpers, addresses):
    """
    In response of GET_UTXO make sure all UTXOs are ordered in the same way; ascending order of seq_no
    """

    address_1, address_2 = addresses
    total = 1000
    outputs = [{"address": address_1, "amount": total}]
    mint_result = helpers.general.do_mint(outputs)

    seq_no = get_seq_no(mint_result)

    remaining = total
    for _ in range(10):
        amount = randint(1, 10)
        inputs = [
            {"address": address_1, "seqNo": seq_no},
        ]
        outputs = [
            {"address": address_2, "amount": amount},
            {"address": address_1, "amount": remaining - amount}
        ]
        request = helpers.request.transfer(inputs, outputs)
        response = helpers.sdk.send_and_check_request_objects([request])
        result = helpers.sdk.get_first_result(response)
        seq_no = get_seq_no(result)
        remaining -= amount

    request = helpers.request.get_utxo(address_2)
    responses = helpers.sdk.send_and_check_request_objects([request])
    for response in responses:
        result = response[1]['result']
        seq_nos = []
        for output in result[OUTPUTS]:
            seq_nos.append(output["seqNo"])

        assert seq_nos == sorted(seq_nos)
