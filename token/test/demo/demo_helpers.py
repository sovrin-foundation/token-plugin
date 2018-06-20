from plenum.server.plugin.token.src.wallet import TokenWallet, Address
from .demo_logger import DemoLogger

demo_logger = DemoLogger()


def assert_wallet_amount(wallet, expected_unspent, expected_spent):
    unspent, spent = wallet_total_amount_and_spent(wallet)
    demo_logger.log_blue("{} wallet has spent {} tokens and currently has {} tokens".format(wallet._name, spent, unspent))
    assert unspent == expected_unspent
    assert spent == expected_spent


def wallet_total_amount_and_spent(wallet):
    addresses = wallet.addresses.values()
    unspent = sum((value for address in addresses for value in address.outputs[0].values()), 0)
    spent = sum((value for address in addresses for value in address.outputs[1].values()), 0)
    return unspent,spent


def create_wallet_with_default_identifier(name):
    w = TokenWallet(name)
    w.addIdentifier()
    return w


def create_address_add_wallet_log(wallet):
    address = create_address_add_wallet(wallet)
    demo_logger.log_blue("The address {} was added to {} wallet".format(address, wallet._name))
    return address


def create_address_add_wallet(wallet):
    address = Address()
    wallet.add_new_address(address)
    return address.address
