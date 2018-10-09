# It is assumed the initial minting will give some tokens to the Sovrin
# Foundation and sovtoken seller platform. From then on, exchange will be
# responsible for giving tokens to "users".
import pytest

from plenum.common.exceptions import (RequestNackedException,
                                      RequestRejectedException,
                                      PoolLedgerTimeoutException)
from plenum.common.txn_util import get_seq_no
from sovtoken.test.conftest import build_wallets_from_data
from sovtoken.constants import ADDRESS, AMOUNT, SEQNO


TOKENAMT = int(1e8)
BILLION = int(1e9)


@pytest.fixture
def addresses(helpers):
    return helpers.wallet.create_new_addresses(5)


@pytest.fixture(scope="module")
def wallets_non_existant_dids():
    return build_wallets_from_data([
        ('DID01', 'vdbK9YQGxNHviCOZ7RbOtUgIx9d29XwU'),
        ('DID02', 'sWPSHOH12GEnwLOuQAJgCWBzFER8glUU'),
        ('DID03', 'poIRynSnHJ2JSyBiah7AfXViGPfGcZ7Z'),
        ('DID04', 'X2YlFw7ibYIfyB3A7pIBasy4gWpFNTC6'),
    ])


def test_trustee_invalid_minting(helpers, addresses):
    """
    Trustees trying to mint new tokens using invalid output (negative value),
    txn fails
    """
    [address1, address2, *_] = addresses

    outputs = [{ADDRESS: address1, AMOUNT: -20}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)

    outputs = [{ADDRESS: address1, AMOUNT: "100"}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)

    outputs = [{ADDRESS: address1, AMOUNT: 0}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)

    outputs = [{ADDRESS: address1, AMOUNT: 20.5}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)


# What about trust anchors, TGB, do those fail as well?
def test_non_trustee_minting(helpers, steward_wallets, addresses):
    """
    Non trustees (stewards in this case) should not be able to mint new tokens
    """
    [address1, address2, *_] = addresses
    outputs = [{ADDRESS: address1, AMOUNT: 100}, {ADDRESS: address2, AMOUNT: 60}]
    request = helpers.request.mint(outputs)
    request.signatures = {}
    request = helpers.wallet.sign_request(request, steward_wallets)
    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


# where are the trustee signatures coming from? How is the trustee wallet
# created here?
# who can set the number of trustees needed, where is that value configured?
# Is there a mint limit?
def test_less_than_min_trustee_minting(helpers, addresses):
    """
    Less than the required number of trustees participate in minting,
    hence the txn fails
    """
    [address1, address2, *_] = addresses
    outputs = [{ADDRESS: address1, AMOUNT: 100}, {ADDRESS: address2, AMOUNT: 60}]
    request = helpers.request.mint(outputs)
    # Remove one signature.
    request.signatures.popitem()
    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_more_than_min_trustee(capsys, helpers, addresses, increased_trustees):
    """
    Should be able to mint with more than the minimum number of trustees.
    """
    [address1, *_] = addresses
    outputs = [{ADDRESS: address1, AMOUNT: 100}]
    request = helpers.request.mint(outputs)
    request = helpers.wallet.sign_request(request, increased_trustees)

    result = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(result)
    seq_no = get_seq_no(result)

    [address1_utxos, *_] = helpers.general.get_utxo_addresses(addresses)

    assert [{ADDRESS: address1, SEQNO: seq_no, AMOUNT: 100}] == address1_utxos


def test_stewards_with_trustees(helpers, addresses, steward_wallets):
    [address1, address2, *_] = addresses

    outputs = [{ADDRESS: address1, AMOUNT: 1000}, {ADDRESS: address2, AMOUNT: 1000}]
    request = helpers.request.mint(outputs)
    # Remove 1 Trustees' signature, assumption is that there were exactly the number of trustees required
    request.signatures.popitem()
    # Add a steward in place of the removed Trustee
    request = helpers.wallet.sign_request(request, steward_wallets[0:1])

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_non_existant_did_with_trustees(
    helpers,
    addresses,
    wallets_non_existant_dids
):
    [address1, address2, *_] = addresses
    signing_wallets = wallets_non_existant_dids[0:1]

    outputs = [{ADDRESS: address1, AMOUNT: 1000}, {ADDRESS: address2, AMOUNT: 1000}]
    request = helpers.request.mint(outputs)
    request = helpers.wallet.sign_request(request, signing_wallets)

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_non_existant_dids(helpers, addresses, wallets_non_existant_dids):
    [address1, address2, *_] = addresses

    outputs = [{ADDRESS: address1, AMOUNT: 1000}, {ADDRESS: address2, AMOUNT: 1000}]
    request = helpers.request.mint(outputs)

    request.signatures = {}
    request = helpers.wallet.sign_request(request, wallets_non_existant_dids)

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_repeat_trustee(helpers, addresses):
    """
        Should not be possible to use the same trustee more than once
    """
    [address1, address2, *_] = addresses
    outputs = [{ADDRESS: address1, AMOUNT: 100}, {ADDRESS: address2, AMOUNT: 60}]
    request = helpers.request.mint(outputs)
    request.signatures.popitem()
    (did, sig) = request.signatures.popitem()
    request.signatures[did] = sig

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_invalid_address(helpers, addresses):
    """
    Minting fails when address is incorrect format.
    """

    invalid_address = "CKRdjCxMb7oXYos33fugTVw3RWAi5MGmEf4n"
    outputs = [{ADDRESS: invalid_address, AMOUNT: 100}]

    with pytest.raises(RequestNackedException):
        result = helpers.general.do_mint(outputs)


def test_trustee_valid_minting(helpers, addresses):
    """
    Trustees should mint new tokens increasing the balance of `SF_MASTER`
    and seller_address
    """
    [address1, address2, *_] = addresses
    total_mint = 10 * BILLION * TOKENAMT
    sf_master_gets = 6 * BILLION * TOKENAMT
    remaining = total_mint - sf_master_gets
    outputs = [{ADDRESS: address1, AMOUNT: sf_master_gets}, {ADDRESS: address2, AMOUNT: remaining}]
    result = helpers.general.do_mint(outputs)
    mint_seq_no = get_seq_no(result)

    [
        address1_utxos,
        address2_utxos
    ] = helpers.general.get_utxo_addresses([address1, address2])

    assert address1_utxos == [{ADDRESS: address1, SEQNO: mint_seq_no, AMOUNT: sf_master_gets}]
    assert address2_utxos == [{ADDRESS: address2, SEQNO: mint_seq_no, AMOUNT: remaining}]


def test_two_mints_to_same_address(addresses, helpers):

    outputs = [{ADDRESS: address, AMOUNT: 100} for address in addresses]
    first_mint_result = helpers.general.do_mint(outputs)
    outputs = [{ADDRESS: address, AMOUNT: 200} for address in addresses]
    second_mint_result = helpers.general.do_mint(outputs)
    first_mint_seq_no = get_seq_no(first_mint_result)
    second_mint_seq_no = get_seq_no(second_mint_result)

    [address1, address2, address3, address4, address5] = addresses

    [
        address1_utxos,
        address2_utxos,
        address3_utxos,
        address4_utxos,
        address5_utxos
    ] = helpers.general.get_utxo_addresses(addresses)

    assert first_mint_seq_no != second_mint_seq_no

    assert address1_utxos == [
        {ADDRESS: address1, SEQNO: first_mint_seq_no, AMOUNT: 100},
        {ADDRESS: address1, SEQNO: second_mint_seq_no, AMOUNT: 200},
    ]
    assert address2_utxos == [
        {ADDRESS: address2, SEQNO: first_mint_seq_no, AMOUNT: 100},
        {ADDRESS: address2, SEQNO: second_mint_seq_no, AMOUNT: 200},
    ]
    assert address3_utxos == [
        {ADDRESS: address3, SEQNO: first_mint_seq_no, AMOUNT: 100},
        {ADDRESS: address3, SEQNO: second_mint_seq_no, AMOUNT: 200},
    ]
    assert address4_utxos == [
        {ADDRESS: address4, SEQNO: first_mint_seq_no, AMOUNT: 100},
        {ADDRESS: address4, SEQNO: second_mint_seq_no, AMOUNT: 200},
    ]
    assert address5_utxos == [
        {ADDRESS: address5, SEQNO: first_mint_seq_no, AMOUNT: 100},
        {ADDRESS: address5, SEQNO: second_mint_seq_no, AMOUNT: 200},
    ]


def test_mint_duplicate_address_single_mint(helpers, addresses):
    """
    Can't mint with duplicate address.
    """

    [address1, address2, *_] = addresses
    outputs = [
        {ADDRESS: address1, AMOUNT: 100},
        {ADDRESS: address2, AMOUNT: 100},
        {ADDRESS: address1, AMOUNT: 100}
    ]

    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)


def test_different_mint_amounts(helpers):

    i64 = 9223372036854775807

    def assert_valid_minting(helpers, amount):
        address = helpers.wallet.create_address()
        outputs = [{ADDRESS: address, AMOUNT: amount}]
        result = helpers.general.do_mint(outputs)
        utxos = helpers.general.get_utxo_addresses([address])[0]

        expected = {ADDRESS: address, SEQNO: get_seq_no(result), AMOUNT: amount}
        matches = [utxo for utxo in utxos if utxo is expected]

    # 1 sovatom
    assert_valid_minting(helpers, 1)

    # 10 billion tokens
    assert_valid_minting(helpers, 10 * BILLION * TOKENAMT)

    # i64 max sovatoms.
    assert_valid_minting(helpers, i64)

    # ujson has a limit at deserializing i64.
    with pytest.raises(PoolLedgerTimeoutException):
        assert_valid_minting(helpers, i64 + 1)


def test_repeat_mint(helpers, addresses):
    """
    Can't use the same mint request twice.
    """
    address = addresses[0]
    outputs = [{ADDRESS: address, AMOUNT: 100}]
    request = helpers.request.mint(outputs)

    helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.send_and_check_request_objects([request])

    seq_no_1 = get_seq_no(helpers.sdk.get_first_result(result))
    utxos = helpers.general.get_utxo_addresses([address])[0]

    assert utxos == [{ADDRESS: address, AMOUNT: 100, SEQNO: seq_no_1}]
