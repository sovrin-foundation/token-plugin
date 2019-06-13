from collections import OrderedDict

import pytest

from indy_common.state import config
from sovtoken.sovtoken_auth_map import sovtoken_auth_map
from sovtokenfees.sovtokenfees_auth_map import sovtokenfees_auth_map

from plenum.common.types import OPERATION

from indy_common.authorize.auth_actions import ADD_PREFIX, EDIT_PREFIX
from indy_common.authorize.auth_constraints import ROLE, ConstraintCreator
from indy_common.authorize.auth_map import auth_map
from indy_common.constants import NYM, TRUST_ANCHOR, AUTH_ACTION, AUTH_TYPE, FIELD, NEW_VALUE, \
    OLD_VALUE, GET_AUTH_RULE, SCHEMA, CONSTRAINT
from indy_node.server.config_req_handler import ConfigReqHandler
from indy_node.test.auth_rule.helper import generate_constraint_list, generate_constraint_entity, \
    sdk_send_and_check_auth_rule_request, sdk_send_and_check_get_auth_rule_request, \
    sdk_send_and_check_get_auth_rule_invalid_request
from plenum.common.constants import TXN_TYPE, TRUSTEE, STEWARD, DATA, STATE_PROOF
from plenum.common.exceptions import RequestNackedException


def generate_key(auth_action=ADD_PREFIX, auth_type=NYM,
                 field=ROLE, new_value=TRUST_ANCHOR,
                 old_value=None):
    key = {AUTH_ACTION: auth_action,
           AUTH_TYPE: auth_type,
           FIELD: field,
           NEW_VALUE: new_value,
           }
    if old_value:
        key[OLD_VALUE] = old_value
    return key


def test_fail_get_auth_rule_with_incorrect_key(looper,
                                               sdk_wallet_trustee,
                                               sdk_pool_handle):
    key = generate_key()
    key[AUTH_TYPE] = "wrong_txn_type"
    with pytest.raises(RequestNackedException, match="Unknown authorization rule: key .* "
                                                     "is not found in authorization map."):
        sdk_send_and_check_get_auth_rule_invalid_request(looper,
                                                         sdk_pool_handle,
                                                         sdk_wallet_trustee,
                                                         **key)[0]

    del key[AUTH_TYPE]
    with pytest.raises(RequestNackedException, match="Not enough fields to build an auth key."):
        sdk_send_and_check_get_auth_rule_invalid_request(looper,
                                                         sdk_pool_handle,
                                                         sdk_wallet_trustee,
                                                         **key)[0]


def test_get_one_auth_rule_transaction(looper,
                                       sdk_wallet_trustee,
                                       sdk_pool_handle):
    key = generate_key()
    str_key = ConfigReqHandler.get_auth_key(key)
    req, resp = sdk_send_and_check_get_auth_rule_request(looper,
                                                         sdk_pool_handle,
                                                         sdk_wallet_trustee,
                                                         **key)[0]

    result = resp["result"][DATA][0]
    assert len(resp["result"][DATA]) == 1
    _check_key(key, result)
    assert result[CONSTRAINT] == auth_map.get(str_key).as_dict


def test_get_one_disabled_auth_rule_transaction(looper,
                                                sdk_wallet_trustee,
                                                sdk_pool_handle):
    key = generate_key(auth_action=EDIT_PREFIX, auth_type=SCHEMA,
                       field='*', old_value='*', new_value='*')
    req, resp = sdk_send_and_check_get_auth_rule_request(looper,
                                                         sdk_pool_handle,
                                                         sdk_wallet_trustee,
                                                         **key)[0]
    result = resp["result"][DATA]
    assert len(result) == 1
    _check_key(key, result[0])
    assert result[0][CONSTRAINT] == {}


def test_get_all_auth_rule_transactions(looper,
                                        sdk_wallet_trustee,
                                        sdk_pool_handle):
    resp = sdk_send_and_check_get_auth_rule_request(looper,
                                                    sdk_pool_handle,
                                                    sdk_wallet_trustee)
    result = resp[0][1]["result"][DATA]
    full_auth_map = OrderedDict(auth_map)
    full_auth_map.update(sovtoken_auth_map)
    full_auth_map.update(sovtokenfees_auth_map)

    for i, (auth_key, constraint) in enumerate(full_auth_map.items()):
        rule = result[i]
        assert auth_key == ConfigReqHandler.get_auth_key(rule)
        if constraint is None:
            assert {} == rule[CONSTRAINT]
        else:
            assert constraint.as_dict == rule[CONSTRAINT]


def test_get_one_auth_rule_transaction_after_write(looper,
                                                   sdk_wallet_trustee,
                                                   sdk_pool_handle):
    auth_action = ADD_PREFIX
    auth_type = NYM
    field = ROLE
    new_value = TRUST_ANCHOR
    constraint = generate_constraint_list(auth_constraints=[generate_constraint_entity(role=TRUSTEE),
                                                            generate_constraint_entity(role=STEWARD)])
    resp = sdk_send_and_check_auth_rule_request(looper,
                                                sdk_pool_handle,
                                                sdk_wallet_trustee,
                                                auth_action=auth_action, auth_type=auth_type,
                                                field=field, new_value=new_value,
                                                constraint=constraint)
    dict_auth_key = generate_key(auth_action=auth_action, auth_type=auth_type,
                                 field=field, new_value=new_value)
    resp = sdk_send_and_check_get_auth_rule_request(looper,
                                                    sdk_pool_handle,
                                                    sdk_wallet_trustee,
                                                    **dict_auth_key)
    result = resp[0][1]["result"][DATA][0]
    assert len(resp[0][1]["result"][DATA]) == 1
    _check_key(dict_auth_key, result)
    assert result[CONSTRAINT] == constraint
    assert resp[0][1]["result"][STATE_PROOF]


def test_get_all_auth_rule_transactions_after_write(looper,
                                                    sdk_wallet_trustee,
                                                    sdk_pool_handle):
    auth_action = ADD_PREFIX
    auth_type = NYM
    field = ROLE
    new_value = TRUST_ANCHOR
    auth_constraint = generate_constraint_list(auth_constraints=[generate_constraint_entity(role=TRUSTEE),
                                                            generate_constraint_entity(role=STEWARD)])
    resp = sdk_send_and_check_auth_rule_request(looper,
                                                sdk_pool_handle,
                                                sdk_wallet_trustee,
                                                auth_action=auth_action, auth_type=auth_type,
                                                field=field, new_value=new_value,
                                                constraint=auth_constraint)
    auth_key = ConfigReqHandler.get_auth_key(resp[0][0][OPERATION])
    resp = sdk_send_and_check_get_auth_rule_request(looper,
                                                    sdk_pool_handle,
                                                    sdk_wallet_trustee)
    result = resp[0][1]["result"][DATA]
    full_auth_map = OrderedDict(auth_map)
    full_auth_map.update(sovtoken_auth_map)
    full_auth_map.update(sovtokenfees_auth_map)
    full_auth_map[auth_key] = ConstraintCreator.create_constraint(auth_constraint)

    for i, (auth_key, constraint) in enumerate(full_auth_map.items()):
        rule = result[i]
        assert auth_key == ConfigReqHandler.get_auth_key(rule)
        if constraint is None:
            assert {} == rule[CONSTRAINT]
        else:
            assert constraint.as_dict == rule[CONSTRAINT]


def _check_key(key, resp_key):
    assert key[AUTH_ACTION] in resp_key[AUTH_ACTION]
    assert key[AUTH_TYPE] in resp_key[AUTH_TYPE]
    assert key[FIELD] in resp_key[FIELD]
    assert key[NEW_VALUE] in resp_key[NEW_VALUE]
    if key[AUTH_ACTION] == EDIT_PREFIX:
        assert key[OLD_VALUE] in resp_key[OLD_VALUE]
    else:
        assert OLD_VALUE not in resp_key
