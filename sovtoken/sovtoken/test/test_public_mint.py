# It is assumed the initial minting will give some tokens to the Sovrin
# Foundation and sovtoken seller platform. From then on, exchange will be
# responsible for giving tokens to "users".
import pytest

from plenum.common.exceptions import (RequestNackedException,
                                      RequestRejectedException)
from plenum.common.txn_util import get_seq_no
from sovtoken.test.conftest import build_wallets_from_data


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

    outputs = [[address1, -20], [address2, 100]]
    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)

    outputs = [[address1, "100"], [address2, 100]]
    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)

    outputs = [[address1, 0], [address2, 100]]
    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)

    outputs = [[address1, 20.5], [address2, 100]]
    with pytest.raises(RequestNackedException):
        helpers.general.do_mint(outputs)


# What about trust anchors, TGB, do those fail as well?
def test_non_trustee_minting(helpers, steward_wallets, addresses):
    """
    Non trustees (stewards in this case) should not be able to mint new tokens
    """
    [address1, address2, *_] = addresses
    outputs = [[address1, 100], [address2, 60]]
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
    outputs = [[address1, 100], [address2, 60]]
    request = helpers.request.mint(outputs)
    # Remove one signature.
    request.signatures.popitem()
    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_stewards_with_trustees(helpers, addresses, steward_wallets):
    [address1, address2, *_] = addresses

    outputs = [[address1, 1000], [address2, 1000]]
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

    outputs = [[address1, 1000], [address2, 1000]]
    request = helpers.request.mint(outputs)
    request = helpers.wallet.sign_request(request, signing_wallets)


def test_non_existant_dids(helpers, addresses, wallets_non_existant_dids):
    [address1, address2, *_] = addresses

    outputs = [[address1, 1000], [address2, 1000]]
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
    outputs = [[address1, 100], [address2, 60]]
    request = helpers.request.mint(outputs)
    request.signatures.popitem()
    (did, sig) = request.signatures.popitem()
    request.signatures[did] = sig
    request.signatures[did] = sig
    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_trustee_valid_minting(helpers, addresses):
    """
    Trustees should mint new tokens increasing the balance of `SF_MASTER`
    and seller_address
    """
    [address1, address2, *_] = addresses
    total_mint = 1000000000000000000
    sf_master_gets = 600000000000000000
    remaining = total_mint - sf_master_gets
    outputs = [[address1, sf_master_gets], [address2, remaining]]
    result = helpers.general.do_mint(outputs)
    mint_seq_no = get_seq_no(result)

    [
        address1_utxos,
        address2_utxos
    ] = helpers.general.get_utxo_addresses([address1, address2])

    assert address1_utxos == [{"address": address1.address, "seqNo": mint_seq_no, "amount": sf_master_gets}]
    assert address2_utxos == [{"address": address2.address, "seqNo": mint_seq_no, "amount": remaining}]


def test_two_mints_to_same_address(addresses, helpers):

    outputs = [[address, 100] for address in addresses]
    first_mint_result = helpers.general.do_mint(outputs)
    outputs = [[address, 200] for address in addresses]
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
        {"address": address1.address, "seqNo": first_mint_seq_no, "amount": 100},
        {"address": address1.address, "seqNo": second_mint_seq_no, "amount": 200},
    ]
    assert address2_utxos == [
        {"address": address2.address, "seqNo": first_mint_seq_no, "amount": 100},
        {"address": address2.address, "seqNo": second_mint_seq_no, "amount": 200},
    ]
    assert address3_utxos == [
        {"address": address3.address, "seqNo": first_mint_seq_no, "amount": 100},
        {"address": address3.address, "seqNo": second_mint_seq_no, "amount": 200},
    ]
    assert address4_utxos == [
        {"address": address4.address, "seqNo": first_mint_seq_no, "amount": 100},
        {"address": address4.address, "seqNo": second_mint_seq_no, "amount": 200},
    ]
    assert address5_utxos == [
        {"address": address5.address, "seqNo": first_mint_seq_no, "amount": 100},
        {"address": address5.address, "seqNo": second_mint_seq_no, "amount": 200},
    ]
