# It is assumed the initial minting will give some tokens to the Sovrin
# Foundation and sovtoken seller platform. From then on, exchange will be
# responsible for giving tokens to "users".
import random

import pytest
from base58 import b58decode


from plenum.common.txn_util import get_seq_no
from plenum.common.constants import STEWARD
from plenum.common.exceptions import RequestNackedException, \
    RequestRejectedException
from sovtoken.messages.fields import PublicAddressField
from plenum.test.conftest import get_data_for_role
from sovtoken.test.helper import send_public_mint, \
    do_public_minting, check_output_val_on_all_nodes
from sovtoken.test.conftest import build_wallets_from_data
from sovtoken.test.helper import user1_token_wallet


@pytest.fixture
def addresses(helpers, user1_token_wallet):
    return helpers.wallet.add_new_addresses(user1_token_wallet, 5)


def test_trustee_invalid_minting(nodeSetWithIntegratedTokenPlugin, looper, # noqa
                                 trustee_wallets, SF_address,
                                 seller_address, sdk_pool_handle):
    """
    Trustees trying to mint new tokens using invalid output (negative value),
    txn fails
    """
    outputs = [[SF_address, -20], [seller_address, 100]]
    with pytest.raises(RequestNackedException):
        send_public_mint(looper, trustee_wallets, outputs, sdk_pool_handle)

    outputs = [[SF_address, "100"], [seller_address, 100]]
    with pytest.raises(RequestNackedException):
        send_public_mint(looper, trustee_wallets, outputs, sdk_pool_handle)

    outputs = [[SF_address, 0], [seller_address, 100]]
    with pytest.raises(RequestNackedException):
        send_public_mint(looper, trustee_wallets, outputs, sdk_pool_handle)


def test_trustee_float_minting(nodeSetWithIntegratedTokenPlugin, looper,
                               trustee_wallets, SF_address, seller_address,
                               sdk_pool_handle):
    """
    Trustees trying to mint new tokens using invalid output (floating point value),
    txn fails
    """
    outputs = [[SF_address, 20.5], [seller_address, 100]]
    with pytest.raises(RequestNackedException):
        send_public_mint(looper, trustee_wallets, outputs, sdk_pool_handle)


# What about trust anchors, TGB, do those fail as well?
def test_non_trustee_minting(nodeSetWithIntegratedTokenPlugin, looper,
                             SF_address, seller_address, poolTxnData,
                             sdk_pool_handle):
    """
    Non trustees (stewards in this case) should not be able to mint new tokens
    """
    total_mint = 100
    sf_master_gets = 60
    seller_gets = total_mint - sf_master_gets
    outputs = [[SF_address, sf_master_gets], [seller_address, seller_gets]]
    steward_data = get_data_for_role(poolTxnData, STEWARD)
    steward_wallets = build_wallets_from_data(steward_data)
    with pytest.raises(RequestRejectedException):
        send_public_mint(looper, steward_wallets, outputs, sdk_pool_handle)


# where are the trustee signatures coming from? How is the trustee wallet
# created here?
# who can set the number of trustees needed, where is that value configured?
# Is there a mint limit?
def test_less_than_min_trustee_minting(nodeSetWithIntegratedTokenPlugin, looper,
                                       trustee_wallets, SF_address,
                                       seller_address, sdk_pool_handle):
    """
    Less than the required number of trustees participate in minting,
    hence the txn fails
    """
    total_mint = 100
    sf_master_gets = 60
    seller_gets = total_mint - sf_master_gets
    outputs = [[SF_address, sf_master_gets], [seller_address, seller_gets]]
    with pytest.raises(RequestRejectedException):
        send_public_mint(looper, trustee_wallets[:3], outputs, sdk_pool_handle)


def test_invalid_trustee_scenarios(nodeSetWithIntegratedTokenPlugin, looper,
                                       trustee_wallets, steward_wallets, SF_address,
                                       seller_address, sdk_pool_handle):
    """
        Making sure we fail to mint in different invalid scenarios
    """
    total_mint = 100
    sf_master_gets = 60
    seller_gets = total_mint - sf_master_gets
    outputs = [[SF_address, sf_master_gets], [seller_address, seller_gets]]

    # Using STEWARDS, NOT TRUSTEES
    with pytest.raises(RequestRejectedException):
        send_public_mint(looper, steward_wallets, outputs, sdk_pool_handle)

    # Adding STEWARDS to TRUSTEE list
    wallets = list(trustee_wallets)
    wallets.extend(steward_wallets)
    with pytest.raises(RequestRejectedException):
        send_public_mint(looper, wallets, outputs, sdk_pool_handle)

    # Using DID not on the ledger
    not_on_ledger_wallets = build_wallets_from_data([
        ('DID01', 'vdbK9YQGxNHviCOZ7RbOtUgIx9d29XwU'),
        ('DID02', 'sWPSHOH12GEnwLOuQAJgCWBzFER8glUU'),
        ('DID03', 'poIRynSnHJ2JSyBiah7AfXViGPfGcZ7Z'),
        ('DID04', 'X2YlFw7ibYIfyB3A7pIBasy4gWpFNTC6'),
    ])
    with pytest.raises(RequestNackedException):
        send_public_mint(looper, not_on_ledger_wallets, outputs, sdk_pool_handle)

    # Add non-ledger DID to TRUSTEE list
    wallets = list(trustee_wallets)
    wallets.append(not_on_ledger_wallets[0])
    with pytest.raises(RequestNackedException):
        send_public_mint(looper, wallets, outputs, sdk_pool_handle)

    # Random sets of 4 wallets. Since we only include 3 TRUSTEES, all random
    # samples should fail to mint
    complete_wallet_set = list()
    complete_wallet_set.extend(steward_wallets)
    complete_wallet_set.extend(not_on_ledger_wallets)
    complete_wallet_set.extend(trustee_wallets[:3])

    for _ in range(5):
        wallets = random.sample(complete_wallet_set, 4)
        wallet_data = "["
        for wallet in wallets:
            wallet_data += " {}-{}".format(wallet.name, str(wallet.idsToSigners[wallet.defaultId].seed))

        wallet_data = "FUZZING TEST -- Please examine !! -- " + wallet_data
        with pytest.raises((RequestRejectedException, RequestNackedException), message=wallet_data):
            send_public_mint(looper, wallets, outputs, sdk_pool_handle)


def test_repeat_trustee(nodeSetWithIntegratedTokenPlugin, looper,
                                       trustee_wallets, SF_address,
                                       seller_address, sdk_pool_handle):
    """
        Should not be possible to use the same trustee more than once
    """
    total_mint = 100
    sf_master_gets = 60
    seller_gets = total_mint - sf_master_gets
    outputs = [[SF_address, sf_master_gets], [seller_address, seller_gets]]
    repeating_trustee_wallets = [trustee_wallets[0], trustee_wallets[0], trustee_wallets[0], trustee_wallets[0]]
    with pytest.raises(RequestRejectedException):
        send_public_mint(looper, repeating_trustee_wallets, outputs, sdk_pool_handle)

def test_trustee_valid_minting(nodeSetWithIntegratedTokenPlugin, looper,
                               trustee_wallets, SF_address, seller_address,
                               sdk_pool_handle):
    """
    Trustees should mint new tokens increasing the balance of `SF_MASTER`
    and seller_address
    """
    total_mint = 1000000000000000000
    sf_master_gets = 600000000000000000
    do_public_minting(looper, trustee_wallets, sdk_pool_handle, total_mint,
                      sf_master_gets, SF_address, seller_address)

    assert len(b58decode(seller_address)) == PublicAddressField.length
    assert len(b58decode(SF_address)) == PublicAddressField.length

    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, SF_address,
                                  sf_master_gets)
    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, seller_address,
                                  total_mint - sf_master_gets)




def test_two_mints_have_different_sequence_numbers(addresses, helpers):

    first_mint_outputs = [[address, 100] for address in addresses]
    first_mint_request = helpers.request.mint(first_mint_outputs)
    first_mint_responses = helpers.sdk.send_and_check_request_objects([first_mint_request])
    first_mint_result = helpers.sdk.get_first_result(first_mint_responses)
    first_mint_seq_no = get_seq_no(first_mint_result)

    second_mint_outputs = [[address, 100] for address in addresses]
    second_mint_request = helpers.request.mint(second_mint_outputs)
    second_mint_responses = helpers.sdk.send_and_check_request_objects([second_mint_request])
    second_mint_result = helpers.sdk.get_first_result(second_mint_responses)
    second_mint_seq_no = get_seq_no(second_mint_result)

    assert second_mint_seq_no != first_mint_seq_no


def test_two_mints_to_same_address(addresses, helpers):


    [address1, address2, address3, address4, address5] = addresses

    first_mint_outputs = [[address, 100] for address in addresses]
    first_mint_request = helpers.request.mint(first_mint_outputs)
    first_mint_responses = helpers.sdk.send_and_check_request_objects([first_mint_request])
    first_mint_result = helpers.sdk.get_first_result(first_mint_responses)
    first_mint_seq_no = get_seq_no(first_mint_result)

    second_mint_outputs = [[address, 200] for address in addresses]
    second_mint_request = helpers.request.mint(second_mint_outputs)
    second_mint_responses = helpers.sdk.send_and_check_request_objects([second_mint_request])
    second_mint_result = helpers.sdk.get_first_result(second_mint_responses)
    second_mint_seq_no = get_seq_no(second_mint_result)

    [
        address1_utxos,
        address2_utxos,
        address3_utxos,
        address4_utxos,
        address5_utxos
    ] = helpers.general.get_utxo_addresses(addresses)

    assert address1_utxos == [
        [address1, first_mint_seq_no, 100],
        [address1, second_mint_seq_no, 200],
    ]
    assert address2_utxos == [
        [address2, first_mint_seq_no, 100],
        [address2, second_mint_seq_no, 200],
    ]
    assert address3_utxos == [
        [address3, first_mint_seq_no, 100],
        [address3, second_mint_seq_no, 200],
    ]
    assert address4_utxos == [
        [address4, first_mint_seq_no, 100],
        [address4, second_mint_seq_no, 200],
    ]
    assert address5_utxos == [
        [address5, first_mint_seq_no, 100],
        [address5, second_mint_seq_no, 200],
    ]


