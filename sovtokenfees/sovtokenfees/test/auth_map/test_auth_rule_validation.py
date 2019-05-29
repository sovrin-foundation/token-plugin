import copy

import pytest
from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.authorize.auth_actions import ADD_PREFIX

from indy_common.constants import NYM, ROLE, TRUST_ANCHOR, CONSTRAINT

from plenum.common.constants import STEWARD

from indy_common.authorize import auth_map
from sovtokenfees.constants import FEES_FIELD_NAME, FEES

from plenum.common.exceptions import RequestRejectedException

from indy_node.test.auth_rule.test_get_auth_rule import sdk_send_and_check_get_auth_rule_request, generate_key
from indy_node.server.config_req_handler import ConfigReqHandler
from indy_common.authorize.auth_constraints import IDENTITY_OWNER


def test_add_metadata_with_not_existed_alias(looper,
                                             helpers,
                                             sdk_wallet_trustee,
                                             sdk_pool_handle,
                                             nodeSetWithIntegratedTokenPlugin):
    fees_alias = "add_new_steward"
    current_fees = helpers.general.do_get_fees()
    assert fees_alias not in current_fees[FEES]
    constraint = copy.deepcopy(auth_map.one_trustee_constraint)
    constraint.set_metadata({FEES_FIELD_NAME: fees_alias})
    with pytest.raises(RequestRejectedException, match="does not exist in current fees".format(fees_alias)):
        sdk_send_and_check_auth_rule_request(looper,
                                             sdk_pool_handle,
                                             sdk_wallet_trustee,
                                             auth_action=ADD_PREFIX, auth_type=NYM,
                                             field=ROLE, new_value=STEWARD,
                                             old_value=None, constraint=constraint.as_dict)

def test_add_metadata_with_complex_constraint(looper,
                                              helpers,
                                              sdk_wallet_trustee,
                                              sdk_pool_handle,
                                              nodeSetWithIntegratedTokenPlugin):
    fees_alias = "2222"
    current_fees = helpers.general.do_get_fees()
    assert fees_alias not in current_fees[FEES]

    constraint = copy.deepcopy(auth_map.trust_anchor_or_steward_or_trustee_constraint)
    # set metadata only for the last constraint in OrAuthConstraint
    constraint.auth_constraints[-1].set_metadata({FEES_FIELD_NAME: fees_alias})
    with pytest.raises(RequestRejectedException, match="does not exist in current fees".format(fees_alias)):
        sdk_send_and_check_auth_rule_request(looper,
                                             sdk_pool_handle,
                                             sdk_wallet_trustee,
                                             auth_action=ADD_PREFIX, auth_type=NYM,
                                             field=ROLE, new_value=IDENTITY_OWNER,
                                             old_value=None, constraint=constraint.as_dict)


def test_add_metadata_with_existed_fees_alias(looper,
                                              helpers,
                                              sdk_wallet_trustee,
                                              sdk_pool_handle,
                                              nodeSetWithIntegratedTokenPlugin):
    fees_alias = '3333'
    current_fees = helpers.general.do_get_fees()
    assert fees_alias not in current_fees[FEES]

    helpers.general.do_set_fees({fees_alias: 42}, fill_auth_map=False)

    current_fees = helpers.general.do_get_fees()
    assert fees_alias in current_fees[FEES]

    constraint = copy.deepcopy(auth_map.one_trustee_constraint)
    constraint.set_metadata({FEES_FIELD_NAME: fees_alias})
    sdk_send_and_check_auth_rule_request(looper,
                                         sdk_pool_handle,
                                         sdk_wallet_trustee,
                                         auth_action=ADD_PREFIX, auth_type=NYM,
                                         field=ROLE, new_value=STEWARD,
                                         old_value=None, constraint=constraint.as_dict)

    key = generate_key(auth_action=ADD_PREFIX, auth_type=NYM,
                       field=ROLE, new_value=STEWARD,)
    auth_rule = sdk_send_and_check_get_auth_rule_request(looper,
                                                         sdk_pool_handle,
                                                         sdk_wallet_trustee,
                                                         **key)[0][1]
    assert auth_rule['result']['data'][0][CONSTRAINT]['metadata'][FEES_FIELD_NAME] == fees_alias
