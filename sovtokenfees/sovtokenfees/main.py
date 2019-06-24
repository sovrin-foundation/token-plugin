import functools

from sovtokenfees.constants import ACCEPTABLE_WRITE_TYPES_FEE, ACCEPTABLE_QUERY_TYPES_FEE, ACCEPTABLE_ACTION_TYPES_FEE
from sovtokenfees.req_handlers.batch_handlers.fee_batch_handler import DomainFeeBatchHandler
from sovtokenfees.req_handlers.read_handlers.get_fee_handler import GetFeeHandler
from sovtokenfees.req_handlers.read_handlers.get_fees_handler import GetFeesHandler
from sovtokenfees.req_handlers.write_handlers.set_fees_handler import SetFeesHandler
from sovtokenfees.req_handlers.write_handlers.xfer_fee_handler import XferFeeHandler
from sovtokenfees.req_handlers.fees_utils import BatchFeesTracker
from sovtokenfees.req_handlers.write_handlers.domain_fee_handler import DomainFeeHandler

from plenum.common.ledger_uncommitted_tracker import LedgerUncommittedTracker
from plenum.common.constants import CONFIG_LEDGER_ID

from common.exceptions import LogicError
from sovtoken.constants import UTXO_CACHE_LABEL, XFER_PUBLIC
from sovtokenfees.sovtokenfees_auth_map import sovtokenfees_auth_map

from sovtokenfees.transactions import FeesTransactions
from typing import Any
from sovtokenfees.fees_authorizer import FeesAuthorizer

from plenum.common.constants import DOMAIN_LEDGER_ID, NodeHooks, ReplicaHooks

from indy_common.constants import CONFIG_LEDGER_ID

from plenum.common.txn_util import get_type
from sovtokenfees.client_authnr import FeesAuthNr
from sovtokenfees.three_phase_commit_handling import \
    ThreePhaseCommitHandler
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.client_authnr import TokenAuthNr

from plenum.server.batch_handlers.audit_batch_handler import AuditBatchHandler
from plenum.server.batch_handlers.ts_store_batch_handler import TsStoreBatchHandler


def integrate_plugin_in_node(node):
    token_ledger = node.db_manager.get_ledger(TOKEN_LEDGER_ID)
    token_state = node.db_manager.get_state(TOKEN_LEDGER_ID)

    fees_tracker, token_tracker = register_trackers(token_state, token_ledger)
    node.write_req_validator.auth_map.update(sovtokenfees_auth_map)
    register_req_handlers(node, fees_tracker)
    register_batch_handlers(node, fees_tracker, token_tracker)
    set_callbacks(node, token_tracker)
    fees_authnr = register_authentication(node)
    register_hooks(node, fees_authnr, token_ledger, token_state, fees_tracker)
    return node


def register_req_handlers(node, fees_tracker):
    node.write_manager.register_req_handler(SetFeesHandler(node.db_manager,
                                                           node.write_req_validator))

    if XFER_PUBLIC not in node.write_manager.request_handlers:
        raise ImportError('sovtoken plugin should be loaded, request '
                          'handler not found')
    node.write_manager.remove_req_handler(XFER_PUBLIC)
    node.write_manager.register_req_handler(XferFeeHandler(node.db_manager,
                                                           node.write_req_validator))

    for typ in list(node.write_manager.ledger_id_to_types[DOMAIN_LEDGER_ID]):
        # Ugly hack, replace it with expanding register_req_handler method
        # TODO: Additional functionality to request_manager ^^^
        domain_fee_r_h = DomainFeeHandler(node.db_manager, fees_tracker)
        domain_fee_r_h.txn_type = typ
        node.write_manager.register_req_handler(domain_fee_r_h)

    node.read_manager.register_req_handler(GetFeeHandler(node.db_manager))
    node.read_manager.register_req_handler(GetFeesHandler(node.db_manager))


def register_batch_handlers(node, fees_tracker, token_tracker):
    handlers = node.write_manager.batch_handlers[DOMAIN_LEDGER_ID]
    node.write_manager.remove_batch_handler(DOMAIN_LEDGER_ID)

    # Temp checks, remove after integration
    if len(handlers) != 4 or not isinstance(handlers[-1], TsStoreBatchHandler) \
            or not (handlers[-2], AuditBatchHandler):
        raise LogicError

    handlers.insert(handlers.index(handlers[-2]),
                    DomainFeeBatchHandler(node.db_manager, fees_tracker, token_tracker))

    for h in handlers:
        if isinstance(h, (AuditBatchHandler, TsStoreBatchHandler)):
            node.write_manager.register_batch_handler(h, ledger_id=DOMAIN_LEDGER_ID)
        node.write_manager.register_batch_handler(h)
    # TODO: Additional functionality to request_manager ^^^


def set_callbacks(node, token_tracker):
    set_post_catchup_callback(node, token_tracker)
    set_post_added_txn_callback(node)


def set_post_catchup_callback(node, token_tracker):
    token_ledger = node.db_manager.get_ledger(TOKEN_LEDGER_ID)
    token_state = node.db_manager.get_state(TOKEN_LEDGER_ID)

    def postCatchupCompleteClbk():
        token_tracker.set_last_committed(token_state.committedHeadHash,
                                         token_ledger.uncommitted_root_hash,
                                         token_ledger.size)

    origin_token_clb = node.ledgerManager.ledgerRegistry[TOKEN_LEDGER_ID].postCatchupCompleteClbk

    def postCatchupCompleteClb(origin_clb):
        if origin_clb:
            origin_clb()
        postCatchupCompleteClbk()

    node.ledgerManager.ledgerRegistry[TOKEN_LEDGER_ID].postCatchupCompleteClbk = \
        functools.partial(postCatchupCompleteClb, origin_token_clb)


def set_post_added_txn_callback(node):
    origin_token_post_added_clb = node.ledgerManager.ledgerRegistry[TOKEN_LEDGER_ID].postTxnAddedToLedgerClbk

    def filter_fees(ledger_id: int, txn: Any):
        origin_token_post_added_clb(ledger_id, txn, get_type(txn) != FeesTransactions.FEES.value)

    node.ledgerManager.ledgerRegistry[TOKEN_LEDGER_ID].postTxnAddedToLedgerClbk = filter_fees


def register_authentication(node):
    utxo_cache = node.db_manager.get_store(UTXO_CACHE_LABEL)
    token_authnr = node.clientAuthNr.get_authnr_by_type(TokenAuthNr)
    if not token_authnr:
        raise ImportError('sovtoken plugin should be loaded, '  # noqa
                          'authenticator not found')
    fees_authnr = FeesAuthNr(ACCEPTABLE_WRITE_TYPES_FEE, ACCEPTABLE_QUERY_TYPES_FEE, ACCEPTABLE_ACTION_TYPES_FEE,
                             node.getState(DOMAIN_LEDGER_ID), token_authnr)
    node.clientAuthNr.register_authenticator(fees_authnr)
    fees_authorizer = FeesAuthorizer(config_state=node.getState(CONFIG_LEDGER_ID),
                                     utxo_cache=utxo_cache)
    node.write_req_validator.register_authorizer(fees_authorizer)
    return fees_authnr


def register_hooks(node, fees_authnr, token_ledger, token_state, fees_tracker):
    register_auth_hooks(node, fees_authnr)
    register_three_pc_hooks(node, token_ledger, token_state, fees_tracker)


def register_auth_hooks(node, fees_authnr):
    node.register_hook(NodeHooks.PRE_SIG_VERIFICATION, fees_authnr.verify_signature)


def register_three_pc_hooks(node, token_ledger, token_state, fees_tracker):
    three_pc_handler = ThreePhaseCommitHandler(node.master_replica,
                                               token_ledger,
                                               token_state,
                                               fees_tracker)
    node.master_replica.register_hook(ReplicaHooks.CREATE_PPR,
                                      three_pc_handler.add_to_pre_prepare)
    node.master_replica.register_hook(ReplicaHooks.CREATE_PR,
                                      three_pc_handler.add_to_prepare)
    node.master_replica.register_hook(ReplicaHooks.CREATE_ORD,
                                      three_pc_handler.add_to_ordered)
    node.master_replica.register_hook(ReplicaHooks.APPLY_PPR,
                                      three_pc_handler.check_recvd_pre_prepare)


def register_trackers(token_state, token_ledger):
    # TODO: move trackers into write_manager
    fees_tracker = BatchFeesTracker()
    token_tracker = LedgerUncommittedTracker(token_state.committedHeadHash,
                                             token_ledger.uncommitted_root_hash,
                                             token_ledger.size)
    return fees_tracker, token_tracker
