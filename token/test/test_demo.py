from ledger.util import F
# from plenum.test.pool_transactions.conftest import clientAndWallet1, client1Connected, \
#     wallet1, looper, client1


import pytest
from plenum.test.plugin.token.helper import do_public_minting, send_xfer, check_output_val_on_all_nodes, send_get_utxo

from .demo.demo_helpers import *
demo_logger.log_green('Performing some setup')

NEW_TOKENS = 100000
SELLER_RECEIVES = 35000
SF_RECEIVES = NEW_TOKENS - SELLER_RECEIVES
RECIPIENT_RECEIVES = 10000

wallet_names = ["Sender", "Recipient", "SF"]
wallets = {wallet_name: create_wallet_with_default_identifier(wallet_name) for wallet_name in wallet_names}
addresses = {wallet_name:create_address_add_wallet_log(wallet) for wallet_name,wallet in wallets.items()}

@pytest.fixture(scope='session', autouse=True)
def setup_teardown():
    demo_logger.log_green('Starting test\n')
    yield
    demo_logger.log_green('Test ended')

@pytest.fixture(scope='module')
def public_mint(trustee_wallets, looper, txnPoolNodeSet, client1, client1Connected):
    resp = do_public_minting(looper, trustee_wallets, client1, NEW_TOKENS,
                      SF_RECEIVES, addresses["SF"], addresses["Sender"])
    demo_logger.log_blue("You have minted {:,} tokens.".format(NEW_TOKENS))
    demo_logger.log_blue("The seller address, {} received {:,} tokens.".format(addresses["Sender"], SELLER_RECEIVES))
    demo_logger.log_blue("The SF address, {} received {:,} tokens".format(addresses["SF"], SF_RECEIVES))
    for wallet in wallets.values():
        wallet._update_outputs(resp['outputs'], resp['seqNo'])
    return resp

@pytest.fixture(scope='module')
def xfer_partial(public_mint, looper, client1, txnPoolNodeSet):
    seq_no = public_mint[F.seqNo.name]
    inputs = [[wallets["Sender"], addresses["Sender"], seq_no]]
    outputs = [[addresses["Sender"], SELLER_RECEIVES - RECIPIENT_RECEIVES], [addresses["Recipient"], RECIPIENT_RECEIVES]]
    demo_logger.log_blue("The Sender is sending {} tokens ot the Recipient".format(RECIPIENT_RECEIVES))
    req = send_xfer(looper, inputs, outputs, client1)
    check_output_val_on_all_nodes(txnPoolNodeSet, addresses["Sender"], SELLER_RECEIVES - RECIPIENT_RECEIVES)
    check_output_val_on_all_nodes(txnPoolNodeSet, addresses["Recipient"], RECIPIENT_RECEIVES)
    result, _ = client1.getReply(req.identifier, req.reqId)
    return result

def test_demo(xfer_partial):
    for wallet in wallets.values():
        wallet.handle_xfer(xfer_partial)

def test_sender_wallet():
    assert_wallet_amount(wallets["Sender"], SELLER_RECEIVES - RECIPIENT_RECEIVES, SELLER_RECEIVES)

def test_recipient_wallet():
    assert_wallet_amount(wallets["Recipient"], RECIPIENT_RECEIVES, 0)

def test_sf_wallet():
    assert_wallet_amount(wallets["SF"], SF_RECEIVES, 0)