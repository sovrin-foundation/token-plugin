import pytest

from plenum.common.txn_util import get_seq_no
from sovtoken.util import update_token_wallet_with_result
from sovtoken.test.helper import do_public_minting, send_xfer, check_output_val_on_all_nodes, send_get_utxo

from sovtoken.test.demo.demo_helpers import *
demo_logger.log_green('Performing some setup')

NEW_TOKENS = 100000
SELLER_RECEIVES = 35000
SF_RECEIVES = NEW_TOKENS - SELLER_RECEIVES
RECIPIENT_RECEIVES = 10000

wallet_names = ["Sender", "Recipient", "SF"]
wallets = {wallet_name: create_wallet_with_default_identifier(wallet_name) for wallet_name in wallet_names}
addresses = {wallet_name:create_address_add_wallet_log(wallet) for wallet_name,wallet in wallets.items()}


@pytest.fixture(scope='module', autouse=True)
def setup_teardown(looper, sdk_pool_handle, sdk_wallet_client, trustee_wallets):
    demo_logger.log_green('Starting test\n')
    resp = public_mint(looper, sdk_pool_handle, sdk_wallet_client, trustee_wallets)
    xfer_partial_amount(looper, sdk_pool_handle, get_seq_no(resp))
    yield
    demo_logger.log_green('Test ended')


def public_mint(looper, sdk_pool_handle, sdk_wallet_client, trustee_wallets):
    demo_logger.log_blue("Minting {:,} tokens.".format(NEW_TOKENS))

    resp = do_public_minting(looper, trustee_wallets, sdk_pool_handle, NEW_TOKENS,
                             SF_RECEIVES, addresses["SF"], addresses["Sender"])

    demo_logger.log_blue("The seller address, {} received {:,} tokens.".format(addresses["Sender"], SELLER_RECEIVES))
    demo_logger.log_blue("The SF address, {} received {:,} tokens".format(addresses["SF"], SF_RECEIVES))

    for wallet, address in zip(wallets.values(), addresses.values()):
        utxo_resp = send_get_utxo(looper, address, sdk_wallet_client, sdk_pool_handle)
        update_token_wallet_with_result(wallet, utxo_resp)
    return resp


def xfer_partial_amount(looper, sdk_pool_handle, seqNo):
    inputs = [[wallets["Sender"], addresses["Sender"], seqNo]]
    outputs = [[addresses["Sender"], SELLER_RECEIVES - RECIPIENT_RECEIVES], [addresses["Recipient"], RECIPIENT_RECEIVES]]

    demo_logger.log_blue("The Sender is sending {} tokens ot the Recipient".format(RECIPIENT_RECEIVES))

    resp = send_xfer(looper, inputs, outputs, sdk_pool_handle)
    for wallet in wallets.values():
        update_token_wallet_with_result(wallet, resp)


def test_addresses_on_nodes(nodeSetWithIntegratedTokenPlugin):
    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin,addresses["Sender"], SELLER_RECEIVES - RECIPIENT_RECEIVES)
    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, addresses["Recipient"], RECIPIENT_RECEIVES)
    check_output_val_on_all_nodes(nodeSetWithIntegratedTokenPlugin, addresses["SF"], SF_RECEIVES)


def test_sender_wallet():
    print(str(wallets))
    assert_wallet_amount(wallets["Sender"], SELLER_RECEIVES - RECIPIENT_RECEIVES, SELLER_RECEIVES)


def test_recipient_wallet():
    assert_wallet_amount(wallets["Recipient"], RECIPIENT_RECEIVES, 0)


def test_sf_wallet():
    assert_wallet_amount(wallets["SF"], SF_RECEIVES, 0)
