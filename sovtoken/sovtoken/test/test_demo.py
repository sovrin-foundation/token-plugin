import pytest

from plenum.common.txn_util import get_seq_no
from sovtoken.util import update_token_wallet_with_result
from sovtoken.test.demo.demo_helpers import demo_logger, assert_address_contains


SOVATOM = int(1e8)
NEW_TOKENS = int(3e6) * SOVATOM
SOVRIN_TO_USER1 = 10 * SOVATOM
SOVRIN_TO_USER2 = 3 * SOVATOM
USER1_TO_USER2 = int(5 * SOVATOM / 10)

SOVRIN = "Sovrin Foundation"
USER1 = "User 1"
USER2 = "User 2"


def create_addresses(helpers):
    addresses = dict(zip(
        [SOVRIN, USER1, USER2],
        helpers.wallet.create_new_addresses(3)
    ))

    template = "{} created the address {}."
    for name, address in addresses.items():
        demo_logger.log_blue(template.format(name, address))

    return addresses


def mint_tokens(helpers, addresses):
    result = helpers.general.do_mint([{"address": addresses[SOVRIN], "amount": NEW_TOKENS}])
    template = "Minted {} sovatoms to {}."
    demo_logger.log_blue(template.format(NEW_TOKENS, SOVRIN))


def sovrin_sends_tokens(helpers, addresses):
    inputs = [{"address": addresses[SOVRIN], "seqNo": 1}]
    outputs = [
        {"address": addresses[USER1], "amount": SOVRIN_TO_USER1},
        {"address": addresses[USER2], "amount": SOVRIN_TO_USER2},
        {"address": addresses[SOVRIN], "amount": NEW_TOKENS - SOVRIN_TO_USER1 - SOVRIN_TO_USER2},
    ]
    helpers.general.do_transfer(inputs, outputs)

    template = "{} sent {} sovatoms to {}."
    demo_logger.log_blue(template.format(SOVRIN, SOVRIN_TO_USER1, USER1))
    demo_logger.log_blue(template.format(SOVRIN, SOVRIN_TO_USER2, USER2))


def user1_sends_tokens(helpers, addresses):
    inputs = [{"address": addresses[USER1], "seqNo": 2}]
    outputs = [
        {"address": addresses[USER2], "amount": USER1_TO_USER2},
        {"address": addresses[USER1], "amount": SOVRIN_TO_USER1 - USER1_TO_USER2},
    ]
    helpers.general.do_transfer(inputs, outputs)

    template = "{} sent {} sovatoms to {}."
    demo_logger.log_blue(template.format(SOVRIN, SOVRIN_TO_USER1, USER1))


def check_tokens(helpers, addresses):
    expected_sovrin = NEW_TOKENS - SOVRIN_TO_USER1 - SOVRIN_TO_USER2
    expected_user1 = SOVRIN_TO_USER1 - USER1_TO_USER2
    expected_user2 = SOVRIN_TO_USER2 + USER1_TO_USER2

    assert_address_contains(helpers, addresses, SOVRIN, expected_sovrin)
    assert_address_contains(helpers, addresses, USER1, expected_user1)
    assert_address_contains(helpers, addresses, USER2, expected_user2)


def test_transfer(helpers):
    demo_logger.log_header("Started demo")

    addresses = create_addresses(helpers)
    mint_tokens(helpers, addresses)
    sovrin_sends_tokens(helpers, addresses)
    user1_sends_tokens(helpers, addresses)
    check_tokens(helpers, addresses)

    demo_logger.log_header("Ended demo")
