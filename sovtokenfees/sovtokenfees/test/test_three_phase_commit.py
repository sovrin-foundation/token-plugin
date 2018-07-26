from sovtokenfees.test.three_phase_commit_helper import *


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

class TestReceivedPrePrepare(BadHashes):

    def test_no_action_on_token_ledger(self, three_phase_handler, pp_valid):
        # On sovtoken ledger, otherwise would raise exception for no fee data.
        assert not three_phase_handler.check_recvd_pre_prepare(pp_token_ledger(pp_valid))

    def test_no_action_if_no_fee_transactions(self, three_phase_handler):
        pp = PP.create_pre_prepare()
        # No fee txns, otherwise would raise exception for no fee data.
        assert not three_phase_handler.check_recvd_pre_prepare(pp)

    def test_exception_no_plugin_fields_field(self, three_phase_handler, pp_valid):
        pp_without_plugin_fields = pp_remove_plugin_fields(pp_valid)
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_without_plugin_fields)
        assert exp.match(f.PLUGIN_FIELDS.nm)

    def test_exception_no_fees_field(self, three_phase_handler, pp_valid):
        # set plugin fields to empty dict
        pp_without_fees_field = pp_remove_fees_field(pp_valid)
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_without_fees_field)
        assert exp.match(FEES)

    def test_pre_prepare_mismatch_fees_count(self, three_phase_handler, pp_valid):
        pp_mismatched_fees = PP.replace_fees_fields(pp_valid, {FEE_TXNS_IN_BATCH: 5})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_mismatched_fees)
        # Exception contains the actual number of txns and the mismatched number
        assert exp.match(FEE_TXNS_IN_BATCH)
        correct_num_fee_txns = getattr(pp_valid, f.PLUGIN_FIELDS.nm)[FEES][FEE_TXNS_IN_BATCH]
        assert exp.match(str(correct_num_fee_txns))
        assert exp.match(str(5))

    def test_incorrect_state_hash(self, three_phase_handler, pp_valid):
        pp_invalid_state_hash = pp_replace_state_hash(pp_valid, self._bad_hash_serialized())
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_invalid_state_hash)
        assert exp.match(f.STATE_ROOT.nm)
        assert exp.match(str(self._bad_hash_unserialized()))

    def test_incorrect_transaction_hash(self, three_phase_handler, pp_valid):
        pp_invalid_txn_hash = pp_replace_txn_hash(pp_valid, self._bad_hash_serialized())
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_invalid_txn_hash)
        assert exp.match(f.TXN_ROOT.nm)
        assert exp.match(str(self._bad_hash_unserialized()))

    def test_valid_pre_prepare(self, three_phase_handler, pp_valid):
        assert not three_phase_handler.check_recvd_pre_prepare(pp_valid)


class TestHasPluginFields:

    def test_no_plugin_fields(self, three_phase_handler, pp_valid):
        pp_no_plugin_fields = PP.remove_field(pp_valid, f.PLUGIN_FIELDS.nm)
        assert not three_phase_handler._has_plugin_fields(pp_no_plugin_fields)

    def test_has_plugin_fields(self, three_phase_handler, pp_valid):
        assert three_phase_handler._has_plugin_fields(pp_valid)


class TestAddToPrepare:

    def _test_no_changes(self, three_phase_handler, pp_valid, fn_pp_adapter):
        prep = Prep.create_prepare(pp_valid)
        pp_adapted = fn_pp_adapter(pp_valid)
        prep_appended = three_phase_handler.add_to_prepare(prep, pp_adapted)
        assert prep_appended == prep

    def test_no_action_if_token_ledger(self, three_phase_handler, pp_valid):
        self._test_no_changes(three_phase_handler, pp_valid, pp_token_ledger)

    def test_no_action_if_no_plugin_fields(self, three_phase_handler, pp_valid):
        self._test_no_changes(three_phase_handler, pp_valid, pp_remove_plugin_fields)

    def test_no_action_if_no_fees_field(self, three_phase_handler, pp_valid):
        self._test_no_changes(three_phase_handler, pp_valid, pp_remove_fees_field)

    def test_valid_prepare(self, pp_valid, three_phase_handler):
        prep = Prep.create_prepare(pp_valid)
        prep_appended = three_phase_handler.add_to_prepare(prep, pp_valid)
        assert prep_appended != prep
        assert getattr(pp_valid, f.PLUGIN_FIELDS.nm)[FEES] == getattr(pp_valid, f.PLUGIN_FIELDS.nm)[FEES]


class TestAddToOrdered:

    def _test_no_changes(self, three_phase_handler, pp_valid, fn_pp_adapter):
        oc = Ord.create_ordered(pp_valid)
        pp_adapted = fn_pp_adapter(pp_valid)
        prep_appended = three_phase_handler.add_to_ordered(oc, pp_adapted)
        assert prep_appended == oc

    def test_no_action_if_token_ledger(self, three_phase_handler, pp_valid):
        self._test_no_changes(three_phase_handler, pp_valid, pp_token_ledger)

    def test_no_action_if_no_plugin_fields(self, three_phase_handler, pp_valid):
        self._test_no_changes(three_phase_handler, pp_valid, pp_remove_plugin_fields)

    def test_no_action_if_no_fees_field(self, three_phase_handler, pp_valid):
        self._test_no_changes(three_phase_handler, pp_valid, pp_remove_fees_field)

    def test_valid_prepare(self, pp_valid, three_phase_handler):
        ord = Ord.create_ordered(pp_valid)
        prep_appended = three_phase_handler.add_to_prepare(ord, pp_valid)
        assert prep_appended != ord
        assert getattr(pp_valid, f.PLUGIN_FIELDS.nm)[FEES] == getattr(pp_valid, f.PLUGIN_FIELDS.nm)[FEES]


class TestReceivedPrePrepareWithTxn(BadHashes):

    def test_no_action_on_token_ledger(self, three_phase_handler, pp_from_nym_req):
        # On sovtoken ledger, otherwise would raise exception for no fee data.
        assert not three_phase_handler.check_recvd_pre_prepare(pp_token_ledger(pp_from_nym_req))

    def test_no_action_if_no_fee_transactions(self, three_phase_handler):
        pp = PP.create_pre_prepare()
        # No fee txns, otherwise would raise exception for no fee data.
        assert not three_phase_handler.check_recvd_pre_prepare(pp)

    def test_exception_no_plugin_fields_field(self, three_phase_handler, pp_from_nym_req):
        pp_without_plugin_fields = pp_remove_plugin_fields(pp_from_nym_req)
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_without_plugin_fields)
        assert exp.match(f.PLUGIN_FIELDS.nm)

    def test_exception_no_fees_field(self, three_phase_handler, pp_from_nym_req):
        # set plugin fields to empty dict
        pp_without_fees_field = pp_remove_fees_field(pp_from_nym_req)
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_without_fees_field)
        assert exp.match(FEES)

    def test_pre_prepare_mismatch_fees_count(self, three_phase_handler, pp_from_nym_req):
        pp_mismatched_fees = PP.replace_fees_fields(pp_from_nym_req, {FEE_TXNS_IN_BATCH: 5})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_mismatched_fees)
        # Exception contains the actual number of txns and the mismatched number
        assert exp.match(FEE_TXNS_IN_BATCH)
        correct_num_fee_txns = getattr(pp_from_nym_req, f.PLUGIN_FIELDS.nm)[FEES][FEE_TXNS_IN_BATCH]
        assert exp.match(str(correct_num_fee_txns))
        assert exp.match(str(5))

    def test_exception_bad_state_hash(self, three_phase_handler, pp_from_nym_req):
        pp_invalid_state_hash = pp_replace_state_hash(pp_from_nym_req, self._bad_hash_serialized())
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_invalid_state_hash)
        assert exp.match(f.STATE_ROOT.nm)
        assert exp.match(str(self._bad_hash_unserialized()))

    def test_exception_bad_transaction_hash(self, three_phase_handler, pp_from_nym_req):
        pp_invalid_txn_hash = PP.replace_fees_fields(pp_from_nym_req, {f.TXN_ROOT.nm: self._bad_hash_serialized()})
        with pytest.raises(Exception) as exp:
            three_phase_handler.check_recvd_pre_prepare(pp_invalid_txn_hash)
        assert exp.match(f.TXN_ROOT.nm)
        assert exp.match(str(self._bad_hash_unserialized()))

    def test_valid_pre_prepare(self, three_phase_handler, pp_from_nym_req):
        pp_appended = three_phase_handler.add_to_pre_prepare(pp_from_nym_req)
        assert not three_phase_handler.check_recvd_pre_prepare(pp_appended)

