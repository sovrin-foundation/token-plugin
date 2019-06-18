import pytest
from sovtoken import TOKEN_LEDGER_ID
from sovtokenfees.req_handlers.batch_handlers.fee_batch_handler import DomainFeeBatchHandler
from sovtokenfees.static_fee_req_handler import txn_root_serializer

from plenum.common.ledger_uncommitted_tracker import LedgerUncommittedTracker
from sovtoken.test.req_handlers.conftest import utxo_cache


@pytest.fixture
def fee_batch_handler(db_manager, fees_tracker, utxo_cache):
    return DomainFeeBatchHandler(db_manager, fees_tracker,
                                 LedgerUncommittedTracker(db_manager.get_state(TOKEN_LEDGER_ID).committedHeadHash,
                                                          db_manager.get_ledger(TOKEN_LEDGER_ID).committed_root_hash,
                                                          db_manager.get_ledger(TOKEN_LEDGER_ID).size)
                                 )
