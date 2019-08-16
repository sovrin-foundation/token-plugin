from sovtokenfees.req_handlers.batch_handlers.fee_batch_handler import DomainFeeBatchHandler

from plenum.common.constants import CONFIG_LEDGER_ID, DOMAIN_LEDGER_ID
from plenum.common.types import f
from sovtoken.constants import ADDRESS, AMOUNT
from sovtokenfees.constants import FEE_TXNS_IN_BATCH, FEES
from sovtoken import TOKEN_LEDGER_ID
from state.trie.pruning_trie import BLANK_ROOT
from sovtokenfees.serializers import state_roots_serializer
from plenum.common.messages.node_messages import PrePrepare, Prepare, Ordered
from plenum.common.util import get_utc_epoch
from sovtokenfees.three_phase_commit_handling import ThreePhaseCommitHandler

import pytest

from plenum.test.helper import init_discarded, create_pre_prepare_params, generate_state_root


@pytest.fixture()
def node(helpers, user_address):
    return helpers.node._nodes[0]


@pytest.fixture()
def domain_batch_fee_handler(node):
    return next(h for h in node.write_manager.batch_handlers[DOMAIN_LEDGER_ID] if isinstance(h, DomainFeeBatchHandler))


@pytest.fixture()
def three_phase_handler(node, domain_batch_fee_handler):
    return ThreePhaseCommitHandler(node.master_replica,
                                   node.db_manager.get_ledger(TOKEN_LEDGER_ID),
                                   node.db_manager.get_state(TOKEN_LEDGER_ID),
                                   domain_batch_fee_handler._fees_tracker)


@pytest.fixture()
def pp_valid(monkeypatch, three_phase_handler):
    return PP.fake_pp_with_fees(monkeypatch, three_phase_handler)


@pytest.fixture(scope="module")
def user_address(helpers):
    address = helpers.wallet.create_address()
    outputs = [{ADDRESS: address, AMOUNT: 1000}]
    helpers.general.do_mint(outputs)
    return address


@pytest.fixture(scope="module")
def user_utxos(helpers, user_address):
    return helpers.general.get_utxo_addresses([user_address])[0]


def pp_token_ledger(pp):
    return PP.replace_fields(pp, {f.LEDGER_ID.nm: TOKEN_LEDGER_ID})


def pp_remove_plugin_fields(pp):
    return PP.remove_field(pp, f.PLUGIN_FIELDS.nm)


def pp_remove_fees_field(pp):
    return PP.replace_fields(pp, {f.PLUGIN_FIELDS.nm: {}})


def pp_replace_state_hash(pp, new_hash):
    return PP.replace_fees_fields(pp, {f.STATE_ROOT.nm: new_hash})


def pp_replace_txn_hash(pp, new_hash):
    return PP.replace_fees_fields(pp, {f.TXN_ROOT.nm: new_hash})


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
    def fake_pp(ledger_id=DOMAIN_LEDGER_ID):
        params = create_pre_prepare_params(state_root=generate_state_root(),
                                           ledger_id=ledger_id)
        return PrePrepare(*params)

    @staticmethod
    def fake_pp_without_fees(three_phase_handler, ledger_id=DOMAIN_LEDGER_ID):
        pp = PP.fake_pp(ledger_id=ledger_id)
        pp_with_fees = three_phase_handler.add_to_pre_prepare(pp)
        return pp_with_fees

    @staticmethod
    def fake_pp_with_fees(monkeypatch, three_phase_handler):
        pp = PP.fake_pp()

        def mock_get_state_root(ledger_id):
            if ledger_id == TOKEN_LEDGER_ID:
                return PP.plugin_data[FEES][f.STATE_ROOT.nm]
            else:
                return 'Pulled state root from a different ledger than sovtoken'

        def mock_get_txn_root(ledger_id):
            if ledger_id == TOKEN_LEDGER_ID:
                return PP.plugin_data[FEES][f.TXN_ROOT.nm]
            else:
                return 'Pulled txn root from a different ledger than sovtoken'

        state_root_deserialized = state_roots_serializer.deserialize(PP.plugin_data[FEES][f.STATE_ROOT.nm])
        txn_root_deserialized = state_roots_serializer.deserialize(PP.plugin_data[FEES][f.TXN_ROOT.nm])

        monkeypatch.setattr(three_phase_handler.fees_tracker, 'fees_in_current_batch', 1)
        monkeypatch.setattr(three_phase_handler.master_replica._ordering_service, 'l_stateRootHash', mock_get_state_root)
        monkeypatch.setattr(three_phase_handler.master_replica._ordering_service, 'l_txnRootHash', mock_get_txn_root)
        monkeypatch.setattr(three_phase_handler.token_state._trie, 'root_hash',
                            state_root_deserialized)
        monkeypatch.setattr(three_phase_handler.token_ledger, 'uncommittedRootHash',
                            txn_root_deserialized)

        return three_phase_handler.add_to_pre_prepare(pp)

    @staticmethod
    def from_request(req, three_phase_handler):
        replica = three_phase_handler.master_replica
        args = [
            replica.instId,
            replica.viewNo,
            replica.lastPrePrepareSeqNo + 1,
            get_utc_epoch(),
            [req.digest],
            init_discarded(),
            req.digest,
            DOMAIN_LEDGER_ID,
            replica.stateRootHash(TOKEN_LEDGER_ID),
            replica.txnRootHash(TOKEN_LEDGER_ID),
            0,
            True
        ]
        return PrePrepare(*args)


@tuple_fields_decorator(Prepare)
class Prep:

    @staticmethod
    def create_prepare(pp):
        # Prepare has the following parameters
        prep_args = [
            pp.instId,
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
            pp.instId,
            pp.viewNo,
            pp.reqIdr,
            [],
            pp.ppSeqNo,
            pp.ppTime,
            pp.ledgerId,
            pp.stateRootHash,
            pp.txnRootHash,
            pp.auditTxnRootHash,
            ["Alpha", "Beta"]
        ]

        return Ordered(*ord_args)


class BadHashes:

    def _bad_hash_unserialized(self):
        return b'bad hash with length of 32 bytes'

    def _bad_hash_serialized(self):
        return state_roots_serializer.serialize(self._bad_hash_unserialized())
