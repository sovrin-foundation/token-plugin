import pytest
from sovtokenfees.req_handlers.batch_handlers.fee_batch_handler import DomainFeeBatchHandler


@pytest.fixture
def fee_batch_handler(db_manager_with_config, fees_tracker):
    return DomainFeeBatchHandler(db_manager_with_config, fees_tracker)
