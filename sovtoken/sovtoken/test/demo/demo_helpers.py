from sovtoken.test.wallet import TokenWallet, Address
from .demo_logger import DemoLogger

demo_logger = DemoLogger()


def assert_address_contains(helpers, addresses, name, expected):
    address = addresses[name]
    utxos = helpers.general.get_utxo_addresses([address])[0]
    total = sum(map(lambda utxo: utxo[2], utxos))

    template = "{} address {} has {} sovatoms."
    demo_logger.log_blue(template.format(name, address.address, total))

    assert total == expected
