from common.serializers.serialization import state_roots_serializer
from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.common.types import f
from plenum.server.plugin.fees.src.constants import FEE_TXNS_IN_BATCH, FEES
from plenum.server.plugin.token import TOKEN_LEDGER_ID
from plenum.common.messages.node_messages import PrePrepare
from plenum.common.util import get_utc_epoch, updateNamedTuple
from plenum.server.replica import Replica
from plenum.server.plugin.fees.src.three_phase_commit_handling import ThreePhaseCommitHandler
from plenum.server.plugin.fees.src.static_fee_req_handler import StaticFeesReqHandler

import pytest
import unittest.mock as mock


@pytest.fixture()
def node(nodeSetWithIntegratedTokenPlugin):
    a, _, _, _ = nodeSetWithIntegratedTokenPlugin
    return a


@pytest.fixture()
def static_req_handler(node):
    return node.get_req_handler(CONFIG_LEDGER_ID)


@pytest.fixture()
def three_phase_handler(node, static_req_handler):
    return ThreePhaseCommitHandler(node.master_replica, None, None, static_req_handler)



class TestPrePrepare():

    def create_pre_prepare(self):
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

    def test_no_changes_on_token_ledger(self, three_phase_handler):
        pp = self.create_pre_prepare()
        pp = updateNamedTuple(pp, **{f.LEDGER_ID.nm: TOKEN_LEDGER_ID})
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp == pp_appended

    def test_no_changes_if_no_fee_transactions(self, three_phase_handler):
        pp = self.create_pre_prepare()
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp == pp_appended

    def test_valid_prepare(self, monkeypatch, three_phase_handler):
        plugin_data = {
            FEES: {
                FEE_TXNS_IN_BATCH: 1,
                f.STATE_ROOT.nm: 'fakeStateRoot',
                f.TXN_ROOT.nm: 'fakeTxnRoot',
            }
        }
        
        def mock_get_state_root(ledger_id):
            if ledger_id == TOKEN_LEDGER_ID:
                return plugin_data[FEES][f.STATE_ROOT.nm]
            else:
                return 'Pulled state root from a different ledger than token'

        def mock_get_txn_root(ledger_id):
            if ledger_id == TOKEN_LEDGER_ID:
                return plugin_data[FEES][f.TXN_ROOT.nm]
            else:
                return 'Pulled txn root from a different ledger than token'

        monkeypatch.setattr(three_phase_handler.fees_req_handler, 'fee_txns_in_current_batch', 1)
        monkeypatch.setattr(three_phase_handler.master_replica, 'stateRootHash', mock_get_state_root)
        monkeypatch.setattr(three_phase_handler.master_replica, 'txnRootHash', mock_get_txn_root)

        pp = self.create_pre_prepare()
        pp_appended = three_phase_handler.add_to_pre_prepare(pp)
        assert pp_appended == updateNamedTuple(pp, **{f.PLUGIN_FIELDS.nm: plugin_data})


class TestReceivedPrePrepare():
    def test_no_action_on_token_ledger(self):
        pass

    def test_no_action_if_no_fee_transactions(self):
        pass

    def test_exception_no_plugin_fields_field(self):
        pass

    def test_exception_no_fees_field(self):
        pass

    def test_preprepare_mismatch_fees_count(self):
        pass

    def test_incorrect_state_hash(self):
        pass

    def test_incorrect_transaction_hash(self):
        pass

    def test_valid_pre_prepare(self):
        pass