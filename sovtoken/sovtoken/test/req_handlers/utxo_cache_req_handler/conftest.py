import pytest
from sovtoken import TOKEN_LEDGER_ID
from sovtoken.request_handlers.batch_req_handler.token_batch_handler import TokenBatchHandler


@pytest.fixture(scope="module")
def token_batch_handler(db_manager, utxo_cache):
    return TokenBatchHandler(db_manager, TOKEN_LEDGER_ID, utxo_cache)


