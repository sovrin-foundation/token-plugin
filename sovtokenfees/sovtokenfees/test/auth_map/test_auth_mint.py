import pytest
from sovtoken.constants import ADDRESS, AMOUNT, MINT_PUBLIC

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.authorize.auth_actions import ADD_PREFIX

from indy_common.authorize.auth_constraints import AuthConstraint
from plenum.common.constants import STEWARD


def mint_tokens(helpers, addresses):
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)

@pytest.fixture()
def addresses(helpers):
    return helpers.wallet.create_new_addresses(2)


def test_xfer_set_with_additional_fees(helpers,
                                       addresses,
                                       looper,
                                       sdk_wallet_trustee,
                                       sdk_pool_handle):
    """
    Transfer request with extra set of fees, and fees are set.
    """
    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    helpers.general.do_mint(outputs)

    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_wallet_trustee,
                                         sdk_pool_handle,
                                         auth_action=ADD_PREFIX,
                                         auth_type=MINT_PUBLIC,
                                         field='*',
                                         new_value='*',
                                         constraint=AuthConstraint(role=STEWARD, sig_count=1,
                                                                   need_to_be_owner=False).as_dict)

    outputs = [{ADDRESS: addresses[0], AMOUNT: 1000}]
    helpers.general.do_mint(outputs)
