import json

import pytest
from sovtokenfees.domain import build_path_for_set_fees
from sovtokenfees.req_handlers.write_handlers.set_fees_handler_0_9_3 import SetFeesHandler093


@pytest.fixture(scope="module")
def set_fees_handler_0_9_3(db_manager_with_config, write_auth_req_validator):
    return SetFeesHandler093(db_manager_with_config, write_auth_req_validator)


def test_set_fees_handler_update_state(set_fees_handler_0_9_3, set_fees_txn, fees):
    set_fees_handler_0_9_3.update_state(set_fees_txn, None, None)
    assert json.loads(
        set_fees_handler_0_9_3.state.get(set_fees_handler_0_9_3.fees_state_key.encode(),
                                         isCommitted=False).decode()) == json.loads(fees)
    assert set_fees_handler_0_9_3.state.get(build_path_for_set_fees("nym_alias").encode(), isCommitted=False) is None
    assert set_fees_handler_0_9_3.state.get(build_path_for_set_fees("attrib_alias").encode(),
                                            isCommitted=False) is None
