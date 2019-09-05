import pytest

from plenum.common.txn_util import get_seq_no
from plenum.test.delayers import req_delay
from plenum.test.stasher import delay_rules
from sovtoken import TOKEN_LEDGER_ID
from sovtokenfees.constants import FEES
from sovtokenfees.test.helper import pay_fees


@pytest.fixture
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


@pytest.fixture(scope='function')
def make_tokens(helpers, nodeSetWithIntegratedTokenPlugin, addresses):
    address, address_2 = addresses
    total = 1000
    outputs = [{"address": address_2, "amount": total}]
    helpers.general.do_mint(outputs)


@pytest.fixture(scope='function')
def fees_paid(helpers, nodeSetWithIntegratedTokenPlugin, addresses, fees_set, make_tokens):
    return pay_fees(helpers, fees_set, addresses[1])


@pytest.fixture(scope='function', params=['all_responding', 'one_responding'])
def nodeSetWithOneRespondingNode(request, nodeSetWithIntegratedTokenPlugin, make_tokens, fees_paid):
    if request.param == 'all_responding':
        yield nodeSetWithIntegratedTokenPlugin
    else:
        stashers = [node.clientIbStasher for node in nodeSetWithIntegratedTokenPlugin[1:]]
        with delay_rules(stashers, req_delay()):
            yield nodeSetWithIntegratedTokenPlugin


def test_get_txn_audit_proof_after_txn_with_fees(helpers, addresses, fees_paid, nodeSetWithOneRespondingNode):
    seq_no = get_seq_no(fees_paid[FEES])
    helpers.general.get_txn(str(TOKEN_LEDGER_ID), seq_no)