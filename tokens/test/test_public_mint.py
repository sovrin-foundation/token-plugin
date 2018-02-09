# It is assumed the initial minting will give some tokens to the Sovrin
# Foundation and token seller platform. From then on, exchange will be
# responsible for giving tokens to "users".
import pytest

from plenum.common.constants import STEWARD
from plenum.test.conftest import get_data_for_role
from tokens.test.helper import send_public_mint, \
    do_public_minting, check_output_val_on_all_nodes
from tokens.test.conftest import build_wallets_from_data
from plenum.test.pool_transactions.conftest import clientAndWallet1, \
    client1, wallet1, client1Connected, looper


def test_trustee_negative_minting(looper, nodeSetWithIntegratedTokenPlugin, client1, # noqa
                                  wallet1, client1Connected, trustee_wallets,
                                  SF_address, seller_address):
    """
    Trustees trying to mint new tokens using invalid output (negative value),
    txn fails
    """
    outputs = [[SF_address, -20], [seller_address, 100]]
    with pytest.raises(AssertionError):
        send_public_mint(looper, trustee_wallets, outputs, client1)


def test_trustee_float_minting(looper, nodeSetWithIntegratedTokenPlugin, client1,  # noqa
                                 wallet1, client1Connected, trustee_wallets,
                                 SF_address, seller_address):
    """
    Trustees trying to mint new tokens using invalid output (floating point value),
    txn fails
    """
    outputs = [[SF_address, 20.5], [seller_address, 100]]
    with pytest.raises(AssertionError):
        send_public_mint(looper, trustee_wallets, outputs, client1)


# What about trust anchors, TGB, do those fail as well?
def test_non_trustee_minting(looper, nodeSetWithIntegratedTokenPlugin, client1, # noqa
                               wallet1, client1Connected, SF_address,
                             seller_address, poolTxnData):
    """
    Non trustees (stewards in this case) should not be able to mint new tokens
    """
    total_mint = 100
    sf_master_gets = 60
    seller_gets = total_mint - sf_master_gets
    outputs = [[SF_address, sf_master_gets], [seller_address, seller_gets]]
    steward_data = get_data_for_role(poolTxnData, STEWARD)
    steward_wallets = build_wallets_from_data(steward_data)
    with pytest.raises(AssertionError):
        send_public_mint(looper, steward_wallets, outputs, client1)


# where are the trustee signatures coming from? How is the trustee wallet
# created here?
# who can set the number of trustees needed, where is that value configured?
# Is there a mint limit?
def test_less_than_min_trustee_minting(looper, nodeSetWithIntegratedTokenPlugin, client1, # noqa
                                 wallet1, client1Connected, trustee_wallets,
                                 SF_address, seller_address):
    """
    Less than the required number of trustees participate in minting,
    hence the txn fails
    """
    total_mint = 100
    sf_master_gets = 60
    seller_gets = total_mint - sf_master_gets
    outputs = [[SF_address, sf_master_gets], [seller_address, seller_gets]]
    with pytest.raises(AssertionError):
        send_public_mint(looper, trustee_wallets[:3], outputs, client1)


def test_trustee_valid_minting(looper, nodeSetWithIntegratedTokenPlugin, client1, # noqa
                               wallet1, client1Connected, trustee_wallets,
                               SF_address, seller_address):
    """
    Trustees should mint new tokens increasing the balance of `SF_MASTER`
    and seller_address
    """
    total_mint = 100
    sf_master_gets = 60
    do_public_minting(looper, trustee_wallets, client1, total_mint,
                      sf_master_gets, SF_address, seller_address)
    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, SF_address, sf_master_gets)
    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, seller_address,
                                  total_mint - sf_master_gets)
