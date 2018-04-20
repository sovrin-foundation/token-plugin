from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.common.types import f
from plenum.server.plugin.fees.src.constants import FEE_TXNS_IN_BATCH, FEES
from plenum.server.plugin.token import TOKEN_LEDGER_ID
from state.trie.pruning_trie import BLANK_ROOT
from common.serializers.serialization import state_roots_serializer
from plenum.common.messages.node_messages import PrePrepare, Prepare, Ordered
from plenum.common.util import get_utc_epoch
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
    return PP.valid_pre_prepare(pp, monkeypatch, three_phase_handler)


def pp_token_ledger(pp):
    return PP.replace_fields(pp, {f.LEDGER_ID.nm: TOKEN_LEDGER_ID})


def pp_remove_plugin_fields(pp):
    return PP.remove_field(pp, f.PLUGIN_FIELDS.nm)


def pp_remove_fees_field(pp):
    return PP.replace_fields(pp, {f.PLUGIN_FIELDS.nm: {}})


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
            0,  # instId
            pp.viewNo,
            pp.ppSeqNo,
            pp.ppTime,
            pp.digest,
            pp.stateRootHash,
            pp.txnRootHash
        ]

        return Prepare(*prep_args)


@tuple_fields_decorator(Ordered)
class Ord:

    @staticmethod
    def create_ordered(pp):
        ord_args = [
            0,  # instId
            pp.viewNo,
            pp.reqIdr[:pp.discarded],
            pp.ppSeqNo,
            pp.ppTime,
            pp.ledgerId,
            pp.stateRootHash,
            pp.txnRootHash
        ]

        return Ordered(*ord_args)