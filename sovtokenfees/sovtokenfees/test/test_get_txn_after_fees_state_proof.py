import pytest

from plenum.common.txn_util import get_seq_no
from plenum.test.delayers import req_delay
from plenum.test.stasher import delay_rules
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.constants import AMOUNT, ADDRESS
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
    return helpers.general.do_mint(outputs)


@pytest.fixture(scope='function', params=['XFER', 'FEES', 'MINT'])
def last_txn(request, helpers, nodeSetWithIntegratedTokenPlugin, addresses, fees_set, make_tokens):
    if request.param == 'FEES':
        return pay_fees(helpers, fees_set, addresses[1])[FEES]
    if request.param == 'XFER':
        inputs = helpers.general.get_utxo_addresses(addresses[1:])
        inputs = [utxo for utxos in inputs for utxo in utxos]
        outputs = [{ADDRESS: addresses[0], AMOUNT: 992}]
        return helpers.general.do_transfer(inputs, outputs)
    if request.param == 'MINT':
        return make_tokens


@pytest.fixture(scope='function', params=['all_responding', 'one_responding'])
def nodeSetWithOneRespondingNode(request, nodeSetWithIntegratedTokenPlugin, make_tokens, last_txn):
    if request.param == 'all_responding':
        yield nodeSetWithIntegratedTokenPlugin
    else:
        stashers = [node.clientIbStasher for node in nodeSetWithIntegratedTokenPlugin[1:]]
        with delay_rules(stashers, req_delay()):
            yield nodeSetWithIntegratedTokenPlugin


def test_get_txn_audit_proof_after_txn_with_fees(helpers, addresses, last_txn, nodeSetWithOneRespondingNode):
    seq_no = get_seq_no(last_txn)
    helpers.general.get_txn(str(TOKEN_LEDGER_ID), seq_no)