from sovtoken.test.helper import libsovtoken_address_to_address

from indy_common.constants import NYM


def test_domain_fee_handler_update_state(domain_fee_handler, nym_request_with_fees, nym_txn, payment_address):
    domain_fee_handler.apply_request(nym_request_with_fees, None, nym_txn)

    token_state = domain_fee_handler.token_state
    utxo_cache = domain_fee_handler.utxo_cache

    assert int(token_state.get((libsovtoken_address_to_address(payment_address) + ":2").encode(), isCommitted=False)) == 9
    assert not token_state.get((libsovtoken_address_to_address(payment_address) + ":1").encode(), isCommitted=False)
    assert utxo_cache.get(libsovtoken_address_to_address(payment_address)) == '2:9'
    assert domain_fee_handler._fees_tracker.fees_in_current_batch == 1
    assert domain_fee_handler._fees_tracker.has_deducted_fees(NYM, 1)
