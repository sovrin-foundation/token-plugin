from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.common.types import f
from plenum.server.plugin.fees.src.constants import FEE_TXNS_IN_BATCH, FEES
from plenum.server.plugin.token import TOKEN_LEDGER_ID
from state.trie.pruning_trie import BLANK_ROOT
from common.serializers.serialization import state_roots_serializer
from plenum.common.messages.node_messages import PrePrepare, Prepare
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

@pytest.fixture()
def pp_valid(monkeypatch, three_phase_handler):
    pp = PP.create_pre_prepare()
    yield PP.valid_pre_prepare(pp, monkeypatch, three_phase_handler)


def tuple_fields_decorator(tuple_field_class):
    def tuple_fields_class_decorator(class_to_be_decorated):
        class TupleFieldsDecorator(class_to_be_decorated):
            @staticmethod
            def remove_field(tf, field):
                tf_dict = tf.__dict__
                tf_dict.pop(field)
                return tuple_field_class(**tf_dict)

            @staticmethod
            def replace_fields(tf, fields):
                tf_dict = tf.__dict__
                tf_dict.update(fields)
                return tuple_field_class(**tf_dict)

            @staticmethod
            def replace_fees_fields(tf, fields):
                plugin_fields = getattr(tf, f.PLUGIN_FIELDS.nm)
                return TupleFieldsDecorator.replace_fields(tf, {
                    f.PLUGIN_FIELDS.nm: {
                        **plugin_fields,
                        FEES: {
                            **plugin_fields[FEES],
                            **fields
                        }
                    }
                })

        return TupleFieldsDecorator
    return tuple_fields_class_decorator



@tuple_fields_decorator(PrePrepare)
class PP:
    plugin_data = {
        FEES: {
            FEE_TXNS_IN_BATCH: 1,
            f.STATE_ROOT.nm: state_roots_serializer.serialize(BLANK_ROOT),
            f.TXN_ROOT.nm: 'VNsWDU8rZ9Jz9NF',
        }
    }

    @staticmethod
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

    @staticmethod
    def valid_pre_prepare(pp, monkeypatch, three_phase_handler):

        def mock_get_state_root(ledger_id):
            if ledger_id == TOKEN_LEDGER_ID:
                return PP.plugin_data[FEES][f.STATE_ROOT.nm]
            else:
                return 'Pulled state root from a different ledger than token'

        def mock_get_txn_root(ledger_id):
            if ledger_id == TOKEN_LEDGER_ID:
                return PP.plugin_data[FEES][f.TXN_ROOT.nm]
            else:
                return 'Pulled txn root from a different ledger than token'

        state_root_deserialized = state_roots_serializer.deserialize(PP.plugin_data[FEES][f.STATE_ROOT.nm])
        txn_root_deserialized = state_roots_serializer.deserialize(PP.plugin_data[FEES][f.TXN_ROOT.nm])

        monkeypatch.setattr(three_phase_handler.fees_req_handler, 'fee_txns_in_current_batch', 1)
        monkeypatch.setattr(three_phase_handler.master_replica, 'stateRootHash', mock_get_state_root)
        monkeypatch.setattr(three_phase_handler.master_replica, 'txnRootHash', mock_get_txn_root)
        monkeypatch.setattr(three_phase_handler.fees_req_handler.token_state._trie, 'root_hash',
                            state_root_deserialized)
        monkeypatch.setattr(three_phase_handler.fees_req_handler.token_ledger, 'uncommittedRootHash',
                            txn_root_deserialized)

        return three_phase_handler.add_to_pre_prepare(pp)
    


@tuple_fields_decorator(Prepare)
class Prep:

    @staticmethod
    def create_prepare(pp):
        # Prepare has the following parameters
        prep_args = [
            0, #instId
            pp.viewNo,
            pp.ppSeqNo,
            pp.ppTime,
            pp.digest,
            pp.stateRootHash,
            pp.txnRootHash
        ]

        return Prepare(*prep_args)



class TestPrePrepare():

    def test_no_changes_on_token_ledger(self, three_phase_handler):
        pp = PP.create_pre_prepare()
        pp = updateNamedTuple(pp, **{f.LEDGER_ID.nm: TOKEN_LEDGER_ID})
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp == pp_appended

    def test_no_changes_if_no_fee_transactions(self, three_phase_handler):
        pp = PP.create_pre_prepare()
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp == pp_appended

    def test_valid_prepare(self, monkeypatch, three_phase_handler):
        pp = PP.create_pre_prepare()
        pp_appended = PP.valid_pre_prepare(pp, monkeypatch, three_phase_handler)
        assert pp_appended == updateNamedTuple(pp, **{f.PLUGIN_FIELDS.nm: PP.plugin_data})



class TestReceivedPrePrepare():

    def _bad_hash_unserialized(self):
        return b'this is a bad hash'

    def _bad_hash_serialized(self):
        return state_roots_serializer.serialize(self._bad_hash_unserialized())

    def test_no_action_on_token_ledger(self, three_phase_handler):
        pp = PP.create_pre_prepare()
        # On token ledger, otherwise would raise exception for no fee data.
        pp_token_ledger = PP.replace_fields(pp, {f.LEDGER_ID.nm: TOKEN_LEDGER_ID})
        assert not three_phase_handler.check_recvd_pre_prepare(pp_token_ledger)

    def test_no_action_if_no_fee_transactions(self, monkeypatch, three_phase_handler):
        pp = PP.create_pre_prepare()
        # No fee txns, otherwise would raise exception for no fee data.
        assert not three_phase_handler.check_recvd_pre_prepare(pp)

    def test_exception_no_plugin_fields_field(self, pp_valid, three_phase_handler):
        pp_without_plugin_fields = PP.remove_field(pp_valid, f.PLUGIN_FIELDS.nm)
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_without_plugin_fields)
        assert exp.match(f.PLUGIN_FIELDS.nm)

    def test_exception_no_fees_field(self, pp_valid, three_phase_handler):
        # set plugin fields to empty dict
        pp_without_fees_field =PP.replace_fields(pp_valid, {f.PLUGIN_FIELDS.nm: {}})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_without_fees_field)
        assert exp.match(FEES)

    def test_pre_prepare_mismatch_fees_count(self, pp_valid, three_phase_handler):
        pp_mismatched_fees = PP.replace_fees_fields(pp_valid, {FEE_TXNS_IN_BATCH: 5})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_mismatched_fees)
        # Exception contains the actual number of txns and the mismatched number
        assert exp.match(FEE_TXNS_IN_BATCH)
        correct_num_fee_txns = getattr(pp_valid, f.PLUGIN_FIELDS.nm)[FEES][FEE_TXNS_IN_BATCH]
        assert exp.match(str(correct_num_fee_txns))
        assert exp.match(str(5))

    def test_incorrect_state_hash(self, pp_valid, three_phase_handler):
        pp_invalid_state_hash = PP.replace_fees_fields(pp_valid, {f.STATE_ROOT.nm: self._bad_hash_serialized()})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_invalid_state_hash)
        assert exp.match(f.STATE_ROOT.nm)
        assert exp.match(str(self._bad_hash_unserialized()))

    def test_incorrect_transaction_hash(self, pp_valid, three_phase_handler):
        pp_invalid_txn_hash = PP.replace_fees_fields(pp_valid, {f.TXN_ROOT.nm: self._bad_hash_serialized()})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_invalid_txn_hash)
        assert exp.match(f.TXN_ROOT.nm)
        assert exp.match(str(self._bad_hash_unserialized()))

    def test_valid_pre_prepare(self, pp_valid, three_phase_handler):
        assert not three_phase_handler.check_recvd_pre_prepare(pp_valid)



class TestHasPluginFields:
    def test_no_plugin_fields(self, pp_valid, three_phase_handler):
        pp_no_plugin_fields = PP.remove_field(pp_valid, f.PLUGIN_FIELDS.nm)
        assert not three_phase_handler._has_plugin_fields(pp_no_plugin_fields)

    def test_has_plugin_fields(self, pp_valid, three_phase_handler):
        assert three_phase_handler._has_plugin_fields(pp_valid)


class TestAddToPrepare:
    @pytest.fixture
    def setup(self, pp_valid):
        prep = Prep.create_prepare(pp_valid)
        yield pp_valid, prep

    def test_no_action_if_token_ledger(self, setup, three_phase_handler):
        pp_appended, prep = setup
        pp_token_ledger = PP.replace_fields(pp_appended, {f.LEDGER_ID.nm: TOKEN_LEDGER_ID})
        prep_appended = three_phase_handler.add_to_prepare(prep, pp_token_ledger)
        assert prep_appended == prep

    def test_no_action_if_no_plugin_fields(self, setup, three_phase_handler):
        pp_appended, prep = setup
        pp_no_plugin_fields = PP.remove_field(pp_appended, f.PLUGIN_FIELDS.nm)
        prep_appended = three_phase_handler.add_to_prepare(prep, pp_no_plugin_fields)
        assert prep_appended == prep

    def test_no_action_if_no_fees_field(self, setup, three_phase_handler):
        pp_appended, prep = setup
        pp_no_fees_fields = PP.replace_fields(pp_appended, {f.PLUGIN_FIELDS.nm: {}})
        prep_appended = three_phase_handler.add_to_prepare(prep, pp_no_fees_fields)
        assert prep_appended == prep

    def test_valid_prepare(self, setup, three_phase_handler):
        pp_appended, prep = setup
        prep_appended = three_phase_handler.add_to_prepare(prep, pp_appended)
        assert prep_appended != prep
        assert getattr(pp_appended, f.PLUGIN_FIELDS.nm)[FEES] == getattr(pp_appended, f.PLUGIN_FIELDS.nm)[FEES]
