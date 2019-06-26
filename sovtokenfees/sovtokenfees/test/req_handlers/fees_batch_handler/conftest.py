import pytest
from sovtoken import TOKEN_LEDGER_ID
from sovtokenfees.req_handlers.batch_handlers.fee_batch_handler import DomainFeeBatchHandler

from plenum.common.ledger_uncommitted_tracker import LedgerUncommittedTracker


@pytest.fixture
def fee_batch_handler(db_manager_with_config, fees_tracker, token_tracker):
    return DomainFeeBatchHandler(db_manager_with_config, fees_tracker)


@pytest.fixture
def token_tracker(db_manager_with_config):
    token_tracker = LedgerUncommittedTracker(db_manager_with_config.get_state(TOKEN_LEDGER_ID).committedHeadHash,
                                             db_manager_with_config.get_ledger(TOKEN_LEDGER_ID).committed_root_hash,
                                             db_manager_with_config.get_ledger(TOKEN_LEDGER_ID).size)
    db_manager_with_config.register_new_tracker(TOKEN_LEDGER_ID, token_tracker)
