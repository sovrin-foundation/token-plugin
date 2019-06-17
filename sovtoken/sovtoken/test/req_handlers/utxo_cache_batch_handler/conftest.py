import pytest
from sovtoken.request_handlers.batch_req_handler.utxo_batch_handler import UTXOBatchHandler


@pytest.fixture(scope="module")
def utxo_batch_handler(db_manager, utxo_cache):
    return UTXOBatchHandler(db_manager)
