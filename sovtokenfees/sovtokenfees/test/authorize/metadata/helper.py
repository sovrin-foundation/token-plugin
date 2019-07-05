import json

from indy_common.authorize.auth_actions import AbstractAuthAction, AuthActionAdd
from indy_common.authorize.auth_constraints import AuthConstraint, ConstraintsEnum
from indy_common.authorize.authorizer import AbstractAuthorizer
from indy_common.test.auth.conftest import IDENTIFIERS
from indy_common.types import Request
from plenum.common.constants import TYPE
from plenum.test.helper import randomOperation
from sovtokenfees.constants import FEES_FIELD_NAME
from sovtokenfees.domain import build_path_for_set_fees

PLUGIN_FIELD = FEES_FIELD_NAME


def set_auth_constraint(validator, auth_constraint):
    def _set_to_state(state, constraint):
        if constraint.constraint_id != ConstraintsEnum.ROLE_CONSTRAINT_ID:
            for constr in constraint.auth_constraints:
                _set_to_state(state, constr)
        else:
            fees_alias = constraint.metadata.get(PLUGIN_FIELD, None)
            if fees_alias:
                fees_value = int(fees_alias)
                current_fees = state.get(build_path_for_set_fees(), isCommitted=False) or b'{}'
                current_fees = json.loads(current_fees.decode())
                current_fees.update({fees_alias: fees_value})
                state.set(build_path_for_set_fees().encode(),
                          json.dumps(current_fees).encode())
    if auth_constraint:
        _set_to_state(validator.config_state, auth_constraint)
    validator.auth_cons_strategy.get_auth_constraint = lambda a: auth_constraint


def build_req_and_action(signatures, need_to_be_owner, amount=None):
    sig = None
    sigs = None
    identifier = None

    if signatures:
        role = next(iter(signatures.keys()))
        identifier = IDENTIFIERS[role][0]

    if len(signatures) == 1 and next(iter(signatures.values())) == 1:
        sig = 'signature'
    else:
        sigs = {IDENTIFIERS[role][i]: 'signature' for role, sig_count in signatures.items() for i in range(sig_count)}

    operation = randomOperation()

    req = Request(identifier=identifier,
                  operation=operation,
                  signature=sig,
                  signatures=sigs)
    if amount is not None:
        setattr(req, PLUGIN_FIELD, amount)
    action = AuthActionAdd(txn_type=req.operation[TYPE],
                           field='some_field',
                           value='new_value',
                           is_owner=need_to_be_owner)

    return req, [action]


def validate(auth_constraint,
             valid_actions,
             all_signatures, is_owner, amount,
             write_auth_req_validator,
             write_request_validation):
    set_auth_constraint(write_auth_req_validator,
                        auth_constraint)

    for signatures in all_signatures:
        next_action = (signatures, is_owner, amount)
        expected = is_expected(next_action, valid_actions)
        result = write_request_validation(*build_req_and_action(*next_action))
        assert result == expected, \
            "Expected {} but result is {} for case {} and valid set {}".format(expected, result, next_action,
                                                                               valid_actions)


def is_expected(next_action, valid_actions):
    for valid_action in valid_actions:
        if next_action[1] != valid_action[1]:  # owner
            continue
        if next_action[2] != valid_action[2]:  # amount
            continue
        valid_signatures = valid_action[0]
        next_action_signatures = next_action[0]
        if valid_signatures.items() <= next_action_signatures.items():  # we may have more signatures than required, this is fine
            return True
    return False
