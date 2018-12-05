import pytest

from common.serializers.serialization import state_roots_serializer
from plenum.common.constants import NYM, PROOF_NODES, ROOT_HASH, STATE_PROOF
from plenum.common.exceptions import (RequestNackedException,
                                      RequestRejectedException)
from plenum.common.txn_util import get_seq_no
from sovtoken.constants import OUTPUTS, XFER_PUBLIC, ADDRESS, SEQNO, AMOUNT, MINT_PUBLIC
from sovtoken.test.helper import decode_proof
from sovtokenfees.constants import FEES
from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler
from state.db.persistent_db import PersistentDB
from state.trie.pruning_trie import Trie, rlp_encode
from storage.kv_in_memory import KeyValueStorageInMemory


def test_get_fees_when_no_fees_set(helpers):
    ledger_fees = helpers.general.do_get_fees()[FEES]
    assert ledger_fees == {}
    helpers.node.assert_set_fees_in_memory({})


def test_set_fees_invalid_numeric(helpers):
    """
    Test set fees with invalid numeric amount.
    """
    def _test_invalid_fees(amount):
        fees = {
            NYM: amount,
            XFER_PUBLIC: 5
        }

        with pytest.raises(RequestNackedException):
            helpers.general.do_set_fees(fees)

        ledger_fees = helpers.general.do_get_fees()[FEES]
        assert ledger_fees == {}
        helpers.node.assert_set_fees_in_memory({})

    _test_invalid_fees(-1)
    _test_invalid_fees(5.5)
    _test_invalid_fees("3")
    _test_invalid_fees(None)


def test_fees_can_be_zero(helpers):
    """
    Fees can be set to zero.
    """
    fees = {NYM: 1}
    helpers.general.do_set_fees(fees)

    with pytest.raises(RequestRejectedException):
        result = helpers.general.do_nym()

    fees = {NYM: 0}
    helpers.general.do_set_fees(fees)

    ledger_fees = helpers.general.do_get_fees()[FEES]
    assert fees == ledger_fees
    helpers.node.assert_set_fees_in_memory(fees)

    helpers.general.do_nym()


def test_trustee_set_fees_for_invalid_txns(helpers):
    """
    Fees are not allowed for MINT_PUBLIC
    """
    fees = {
        NYM: 1,
        MINT_PUBLIC: 2
    }
    with pytest.raises(RequestNackedException):
        helpers.general.do_set_fees(fees)
    ledger_fees = helpers.general.do_get_fees()[FEES]
    assert ledger_fees == {}


def test_non_trustee_set_fees(helpers):
    """
    Only trustees can change the sovtokenfees
    """
    fees = {
        NYM: 1,
        XFER_PUBLIC: 2
    }
    fees_request = helpers.request.set_fees(fees)
    fees_request.signatures = None
    fees_request = helpers.wallet.sign_request_stewards(fees_request)
    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([fees_request])
    ledger_fees = helpers.general.do_get_fees()[FEES]
    assert ledger_fees == {}


def test_set_fees_not_enough_trustees(helpers):
    """
    Setting fees requires at least three trustees
    """
    fees = {
        NYM: 1,
        XFER_PUBLIC: 2
    }
    fees_request = helpers.request.set_fees(fees)
    fees_request.signatures.popitem()
    assert len(fees_request.signatures) == 2

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([fees_request])

    ledger_fees = helpers.general.do_get_fees()[FEES]
    assert ledger_fees == {}


def test_set_fees_with_stewards(helpers):
    """
    Setting fees fails with stewards.
    """
    fees = {NYM: 1}
    fees_request = helpers.request.set_fees(fees)
    fees_request.signatures.popitem()
    assert len(fees_request.signatures) == 2

    fees_request = helpers.wallet.sign_request_stewards(
        fees_request,
        number_signers=1
    )
    assert len(fees_request.signatures) == 3

    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([fees_request])

    ledger_fees = helpers.general.do_get_fees()[FEES]
    assert ledger_fees == {}
    helpers.node.assert_set_fees_in_memory({})


def test_trustee_set_valid_fees(helpers, fees_set, fees):
    """
    Set a valid sovtokenfees
    """
    helpers.node.assert_set_fees_in_memory(fees)


def test_get_fees(helpers, fees_set, fees):
    """
    Get the sovtokenfees from the ledger
    """
    ledger_fees = helpers.general.do_get_fees()[FEES]
    assert ledger_fees == fees


def test_change_fees(helpers, fees_set, fees):
    """
    Change the sovtokenfees on the ledger and check that sovtokenfees has
    changed.
    """
    updated_fees = {**fees, NYM: 10}
    helpers.general.do_set_fees(updated_fees)
    ledger_fees = helpers.general.do_get_fees()[FEES]
    assert ledger_fees == updated_fees
    assert ledger_fees != fees
    helpers.node.assert_set_fees_in_memory(updated_fees)


def test_get_fees_with_proof(helpers, fees_set, fees):
    """
    Get the sovtokenfees from the ledger
    """
    result = helpers.general.do_get_fees()
    fees = result[FEES]
    state_proof = result[STATE_PROOF]
    assert state_proof
    proof_nodes = decode_proof(result[STATE_PROOF][PROOF_NODES])
    client_trie = Trie(PersistentDB(KeyValueStorageInMemory()))
    fees = rlp_encode([StaticFeesReqHandler.state_serializer.serialize(fees)])
    assert client_trie.verify_spv_proof(
        state_roots_serializer.deserialize(result[STATE_PROOF][ROOT_HASH]),
        StaticFeesReqHandler.fees_state_key, fees, proof_nodes)


def test_mint_after_set_fees(helpers, fees_set):
    # Try another minting after setting fees
    address = helpers.wallet.create_address()
    outputs = [{ADDRESS: address, AMOUNT: 60}]
    mint_req = helpers.general.do_mint(outputs)
    utxos = helpers.general.do_get_utxo(address)[OUTPUTS]
    assert utxos == [{
        ADDRESS: address,
        SEQNO: get_seq_no(mint_req),
        AMOUNT: 60
    }]
