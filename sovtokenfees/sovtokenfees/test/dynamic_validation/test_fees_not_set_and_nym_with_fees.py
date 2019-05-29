from sovtokenfees.constants import FEES
from sovtokenfees.test.constants import NYM_FEES_ALIAS
from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_nym_with_fees, \
    ensure_all_nodes_have_same_data

from indy_common.constants import NYM

from plenum.test.pool_transactions.helper import sdk_add_new_nym

from indy_common.authorize.auth_map import add_new_identity_owner, auth_map

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.authorize.auth_actions import ADD_PREFIX


def test_fees_not_set_and_nym_with_fees(helpers,
                                        nodeSetWithIntegratedTokenPlugin,
                                        sdk_wallet_steward,
                                        address_main,
                                        sdk_pool_handle,
                                        sdk_wallet_trustee,
                                        mint_tokens,
                                        looper):
    """
    Steps:
    1. Checks that nym with zero fees is valid
    """
    current_amount = get_amount_from_token_txn(mint_tokens)
    seq_no = 1
    fees = {NYM_FEES_ALIAS: 0}
    current_amount, seq_no, _ = send_and_check_nym_with_fees(helpers, {FEES: fees}, seq_no, looper, [address_main],
                                                             current_amount)
    sdk_add_new_nym(looper, sdk_pool_handle, sdk_wallet_steward)
    ensure_all_nodes_have_same_data(looper, nodeSetWithIntegratedTokenPlugin)