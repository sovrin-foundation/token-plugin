import json

from sovtokenfees.domain import build_path_for_set_fees


def test_set_fees_handler_update_state(set_fees_handler, set_fees_txn, fees):
    set_fees_handler.update_state(set_fees_txn, None, None)
    assert json.loads(
        set_fees_handler.state.get(build_path_for_set_fees().encode(), isCommitted=False).decode()) == json.loads(fees)
    assert set_fees_handler.state.get(build_path_for_set_fees("nym_alias").encode(), isCommitted=False).decode() == "1"
    assert set_fees_handler.state.get(build_path_for_set_fees("attrib_alias").encode(),
                                      isCommitted=False).decode() == "2"
