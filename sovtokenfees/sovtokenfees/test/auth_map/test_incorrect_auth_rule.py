from indy_common.authorize.auth_constraints import AuthConstraintForbidden, METADATA
from sovtokenfees.constants import FEES_FIELD_NAME

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_invalid_request
from sovtokenfees.test.auth_map.helper import set_fees
from sovtokenfees.test.constants import NYM_FEES_ALIAS


def test_incorrect_auth_rule(helpers,
                             addresses,
                             looper,
                             sdk_wallet_trustee,
                             sdk_pool_handle):
    set_fees(helpers, {NYM_FEES_ALIAS: 5})
    constraint = AuthConstraintForbidden().as_dict
    constraint[METADATA] = {FEES_FIELD_NAME: NYM_FEES_ALIAS}
    sdk_send_and_check_auth_rule_invalid_request(looper,
                                                 sdk_pool_handle,
                                                 sdk_wallet_trustee,
                                                 constraint=constraint)
