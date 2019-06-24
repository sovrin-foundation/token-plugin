from indy_common.constants import NYM


def test_domain_fee_handler_update_state(domain_fee_handler, nym_request_with_fees, nym_txn, payment_address):
    domain_fee_handler.update_state(nym_txn, None, nym_request_with_fees)

    token_state = domain_fee_handler.token_state
    utxo_cache = domain_fee_handler.utxo_cache

    assert int(token_state.get((payment_address[8:] + ":2").encode(), isCommitted=False)) == 9
    assert not token_state.get((payment_address[8:] + ":1").encode(), isCommitted=False)
    assert utxo_cache.get(payment_address[8:]) == '2:9'
    assert domain_fee_handler._fees_tracker.fees_in_current_batch == 1
    assert domain_fee_handler._fees_tracker.has_deducted_fees(NYM, 1)
