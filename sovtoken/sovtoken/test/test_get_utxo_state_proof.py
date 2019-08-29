from random import randint

import pytest
from plenum.test.stasher import delay_rules
from plenum.test.delayers import req_delay
from sovtoken.constants import UTXO_LIMIT, TOKEN_LEDGER_ID
from sovtoken.request_handlers.token_utils import TokenStaticHelper
from sovtoken.test.helper import libsovtoken_address_to_address


@pytest.fixture
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture(scope='function')
def make_tokens(helpers, nodeSetWithIntegratedTokenPlugin, addresses):
    address, address_2 = addresses
    states = [n.db_manager.get_state(TOKEN_LEDGER_ID) for n in nodeSetWithIntegratedTokenPlugin]
    utxos = []

    for i in range(UTXO_LIMIT+200):
        amount = randint(1, 5)
        seq_no = i+5
        key = TokenStaticHelper.create_state_key(libsovtoken_address_to_address(address), seq_no)
        utxos.append((key, amount, seq_no))
        for state in states:
            state.set(key, str(amount).encode())

    total = 1000
    outputs = [{"address": address_2, "amount": total}]
    helpers.general.do_mint(outputs)


@pytest.fixture(scope='function', params=['all_responding', 'one_responding'])
def nodeSetWithOneRespondingNode(request, nodeSetWithIntegratedTokenPlugin, make_tokens):
    if request.param == 'all_responding':
        yield nodeSetWithIntegratedTokenPlugin
    else:
        stashers = [node.clientIbStasher for node in nodeSetWithIntegratedTokenPlugin[1:]]
        with delay_rules(stashers, req_delay()):
            yield nodeSetWithIntegratedTokenPlugin


def test_state_proof_get_utxo_read(helpers, addresses, make_tokens, nodeSetWithOneRespondingNode):
    address, _ = addresses
    request = helpers.request.get_utxo(address)
    helpers.sdk.send_and_check_request_objects([request])
