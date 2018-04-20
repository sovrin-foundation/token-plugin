from plenum.server.plugin.fees.test.three_phase_commit_helper import *

class TestPrePrepare:

    def test_no_changes_on_token_ledger(self, three_phase_handler):
        pp = PP.create_pre_prepare()
        pp = PP.replace_fields(pp, {f.LEDGER_ID.nm: TOKEN_LEDGER_ID})
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp == pp_appended

    def test_no_changes_if_no_fee_transactions(self, three_phase_handler):
        pp = PP.create_pre_prepare()
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp == pp_appended

    def test_valid_prepare(self, monkeypatch, three_phase_handler):
        pp = PP.create_pre_prepare()
        pp_appended = PP.valid_pre_prepare(pp, monkeypatch, three_phase_handler)
        assert pp_appended == PP.replace_fields(pp, {f.PLUGIN_FIELDS.nm: PP.plugin_data})



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


class TestAddToOrdered:
    @pytest.fixture
    def setup(self, pp_valid):
        oc = Prep.create_prepare(pp_valid)
        yield pp_valid, oc

    def test_no_action_if_token_ledger(self, setup, three_phase_handler):
        pp_valid, oc = setup
        pp_token_ledger = PP.replace_fields(pp_valid, {f.LEDGER_ID.nm: TOKEN_LEDGER_ID})
        oc_appended = three_phase_handler.add_to_ordered(oc, pp_token_ledger)
        assert oc_appended == oc

    def test_no_action_if_no_plugin_fields(self, setup, three_phase_handler):
        pp_valid, oc = setup
        pp_no_plugin_fields = PP.remove_field(pp_valid, f.PLUGIN_FIELDS.nm)
        oc_appended = three_phase_handler.add_to_ordered(oc, pp_no_plugin_fields)
        assert oc_appended == oc

    def test_no_action_if_no_fees_field(self, setup, three_phase_handler):
        pp_valid, oc = setup
        pp_no_fees_fields = PP.replace_fields(pp_valid, {f.PLUGIN_FIELDS.nm: {}})
        oc_appended = three_phase_handler.add_to_ordered(oc, pp_no_fees_fields)
        assert oc_appended == oc

    def test_valid_prepare(self, setup, three_phase_handler):
        pp_valid, oc = setup
        oc_appended = three_phase_handler.add_to_ordered(oc, pp_valid)
        assert oc_appended != oc
        assert getattr(oc_appended, f.PLUGIN_FIELDS.nm)[FEES] == getattr(pp_valid, f.PLUGIN_FIELDS.nm)[FEES]
