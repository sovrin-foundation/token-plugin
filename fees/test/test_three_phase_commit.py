from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.common.types import f
from plenum.server.plugin.fees.src.constants import FEE_TXNS_IN_BATCH, FEES
from plenum.server.plugin.token import TOKEN_LEDGER_ID
from state.trie.pruning_trie import BLANK_ROOT
from common.serializers.serialization import state_roots_serializer
from plenum.common.messages.node_messages import PrePrepare
from plenum.common.util import get_utc_epoch, updateNamedTuple
from plenum.server.plugin.fees.src.three_phase_commit_handling import ThreePhaseCommitHandler

import pytest



@pytest.fixture()
def node(nodeSetWithIntegratedTokenPlugin):
    a, _, _, _ = nodeSetWithIntegratedTokenPlugin
    return a


@pytest.fixture()
def static_req_handler(node):
    return node.get_req_handler(CONFIG_LEDGER_ID)


@pytest.fixture()
def three_phase_handler(node, static_req_handler):
    token_handler = node.get_req_handler(ledger_id=TOKEN_LEDGER_ID)
    return ThreePhaseCommitHandler(node.master_replica, token_handler.ledger, token_handler.state, static_req_handler)


def create_pre_prepare():
    pre_prepare_args = [
        # instIds
        0,
        # viewNo
        0,
        # ppSeqNo
        2,
        # ppTime
        get_utc_epoch(),
        # reqIdr
        [('B8fV7naUqLATYocqu7yZ8W,CA4bVFDU4GLbX8xZju811o,E7QRhdcnhAwA6E46k9EtZo,M9BJDuS24bqbJNvBRsoGg3',
          1524070614801839)],
        # discarded
        1,
        # digest
        'ccb7388bc43a1e4669a23863c2b8c43efa183dde25909541b06c0f5196ac4f3b',
        # ledger id
        2,
        # state root
        '5BU5Rc3sRtTJB6tVprGiTSqiRaa9o6ei11MjH4Vu16ms',
        # txn root
        'EdxDR8GUeMXGMGtQ6u7pmrUgKfc2XdunZE79Z9REEHg6',
    ]

    return PrePrepare(*pre_prepare_args)

PLUGIN_DATA = {
    FEES: {
        FEE_TXNS_IN_BATCH: 1,
        f.STATE_ROOT.nm: state_roots_serializer.serialize(BLANK_ROOT),
        f.TXN_ROOT.nm: 'VNsWDU8rZ9Jz9NF',
    }
}


def valid_pre_prepare(monkeypatch, three_phase_handler, pre_prepare):

    def mock_get_state_root(ledger_id):
        if ledger_id == TOKEN_LEDGER_ID:
            return PLUGIN_DATA[FEES][f.STATE_ROOT.nm]
        else:
            return 'Pulled state root from a different ledger than token'

    def mock_get_txn_root(ledger_id):
        if ledger_id == TOKEN_LEDGER_ID:
            return PLUGIN_DATA[FEES][f.TXN_ROOT.nm]
        else:
            return 'Pulled txn root from a different ledger than token'

    state_root_deserialized = state_roots_serializer.deserialize(PLUGIN_DATA[FEES][f.STATE_ROOT.nm])
    txn_root_deserialized = state_roots_serializer.deserialize(PLUGIN_DATA[FEES][f.TXN_ROOT.nm])

    monkeypatch.setattr(three_phase_handler.fees_req_handler, 'fee_txns_in_current_batch', 1)
    monkeypatch.setattr(three_phase_handler.master_replica, 'stateRootHash', mock_get_state_root)
    monkeypatch.setattr(three_phase_handler.master_replica, 'txnRootHash', mock_get_txn_root)
    monkeypatch.setattr(three_phase_handler.fees_req_handler.token_state._trie, 'root_hash', state_root_deserialized)
    monkeypatch.setattr(three_phase_handler.fees_req_handler.token_ledger, 'uncommittedRootHash', txn_root_deserialized)


    return three_phase_handler.add_to_pre_prepare(pre_prepare)



class TestPrePrepare():

    def test_no_changes_on_token_ledger(self, three_phase_handler):
        pp = create_pre_prepare()
        pp = updateNamedTuple(pp, **{f.LEDGER_ID.nm: TOKEN_LEDGER_ID})
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp == pp_appended

    def test_no_changes_if_no_fee_transactions(self, three_phase_handler):
        pp = create_pre_prepare()
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp == pp_appended

    def test_valid_prepare(self, monkeypatch, three_phase_handler):
        pp = create_pre_prepare()
        pp_appended = valid_pre_prepare(monkeypatch, three_phase_handler, pp)
        assert pp_appended == updateNamedTuple(pp, **{f.PLUGIN_FIELDS.nm: PLUGIN_DATA})


class TestReceivedPrePrepare():
    def _pre_prepare_remove_field(self, pp, field):
        pp_dict = pp.__dict__
        pp_dict.pop(field)
        return PrePrepare(**pp_dict)

    def _pre_prepare_replace_fields(self, pp, fields):
        pp_dict = pp.__dict__
        pp_dict.update(fields)
        return PrePrepare(**pp_dict)

    def _replace_fees_fields(self, pp, fields):
        plugin_fields = getattr(pp, f.PLUGIN_FIELDS.nm)
        return self._pre_prepare_replace_fields(pp, {
            f.PLUGIN_FIELDS.nm: {
                **plugin_fields,
                FEES: {
                    **plugin_fields[FEES],
                    **fields
                }
            }
        })

    def _bad_hash_unserialized(self):
        return b'this is a bad hash'

    def _bad_hash_serialized(self):
        return state_roots_serializer.serialize(self._bad_hash_unserialized())

    def test_no_action_on_token_ledger(self, three_phase_handler):
        pp = create_pre_prepare()
        # On token ledger, otherwise would raise exception for no fee data.
        pp_token_ledger = self._pre_prepare_replace_fields(pp, {f.LEDGER_ID.nm: TOKEN_LEDGER_ID})
        assert not three_phase_handler.check_recvd_pre_prepare(pp_token_ledger)

    def test_no_action_if_no_fee_transactions(self, monkeypatch, three_phase_handler):
        pp = create_pre_prepare()
        # No fee txns, otherwise would raise exception for no fee data.
        assert not three_phase_handler.check_recvd_pre_prepare(pp)

    def test_exception_no_plugin_fields_field(self, monkeypatch, three_phase_handler):
        pp = create_pre_prepare()
        pp_appended = valid_pre_prepare(monkeypatch, three_phase_handler, pp)
        pp_without_plugin_fields = self._pre_prepare_remove_field(pp_appended, f.PLUGIN_FIELDS.nm)
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_without_plugin_fields)
        assert exp.match(f.PLUGIN_FIELDS.nm)

    def test_exception_no_fees_field(self, monkeypatch, three_phase_handler):
        pp = create_pre_prepare()
        pp_appended = valid_pre_prepare(monkeypatch, three_phase_handler, pp)
        # set plugin fields to empty dict
        pp_without_fees_field = self._pre_prepare_replace_fields(pp_appended, {f.PLUGIN_FIELDS.nm: {}})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_without_fees_field)
        assert exp.match(FEES)

    def test_pre_prepare_mismatch_fees_count(self, monkeypatch, three_phase_handler):
        pp = create_pre_prepare()
        pp_appended = valid_pre_prepare(monkeypatch, three_phase_handler, pp)
        pp_mismatched_fees = self._replace_fees_fields(pp_appended, {FEE_TXNS_IN_BATCH: 5})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_mismatched_fees)
        # Exception contains the actual number of txns and the mismatched number
        assert exp.match(FEE_TXNS_IN_BATCH)
        correct_num_fee_txns = getattr(pp_appended, f.PLUGIN_FIELDS.nm)[FEES][FEE_TXNS_IN_BATCH]
        assert exp.match(str(correct_num_fee_txns))
        assert exp.match(str(5))

    def test_incorrect_state_hash(self, monkeypatch, three_phase_handler):
        pp = create_pre_prepare()
        pp_appended = valid_pre_prepare(monkeypatch, three_phase_handler, pp)
        pp_invalid_state_hash = self._replace_fees_fields(pp_appended, {f.STATE_ROOT.nm: self._bad_hash_serialized()})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_invalid_state_hash)
        assert exp.match(f.STATE_ROOT.nm)
        assert exp.match(str(self._bad_hash_unserialized()))

    def test_incorrect_transaction_hash(self, monkeypatch, three_phase_handler):
        pp = create_pre_prepare()
        pp_appended = valid_pre_prepare(monkeypatch, three_phase_handler, pp)
        pp_invalid_txn_hash = self._replace_fees_fields(pp_appended, {f.TXN_ROOT.nm: self._bad_hash_serialized()})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_invalid_txn_hash)
        assert exp.match(f.TXN_ROOT.nm)
        assert exp.match(str(self._bad_hash_unserialized()))

    def test_valid_pre_prepare(self, monkeypatch, three_phase_handler):
        pp = create_pre_prepare()
        pp_appended = valid_pre_prepare(monkeypatch, three_phase_handler, pp)
        assert not three_phase_handler.check_recvd_pre_prepare(pp_appended)