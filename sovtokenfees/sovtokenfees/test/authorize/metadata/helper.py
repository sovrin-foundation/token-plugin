import json
from typing import NamedTuple, List, Optional

from indy_common.authorize.auth_actions import AuthActionAdd
from indy_common.authorize.auth_constraints import ConstraintsEnum
from indy_common.test.auth.conftest import IDENTIFIERS
from indy_common.types import Request
from plenum.common.constants import TYPE
from plenum.test.helper import randomOperation
from sovtokenfees.constants import FEES_FIELD_NAME
from sovtokenfees.domain import build_path_for_set_fees

PLUGIN_FIELD = FEES_FIELD_NAME

Action = NamedTuple('Action',
                    [("author", str), ("endorser", Optional[str]), ("sigs", dict),
                     ("is_owner", bool), ("amount", int), ("extra_sigs", bool)])


def set_auth_constraint(validator, auth_constraint):
    def _set_to_state(state, constraint):
        if constraint.constraint_id == ConstraintsEnum.FORBIDDEN_CONSTRAINT_ID:
            return
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


def build_req_and_action(action: Action):
    sig = None
    sigs = None
    identifier = IDENTIFIERS[action.author][0]
    endorser_did = None

    # if there is only 1 sig from the Author - use `signature` instead of `signatures`
    if len(action.sigs) == 1 and next(iter(action.sigs.values())) == 1 and next(
            iter(action.sigs.keys())) == action.author:
        sig = 'signature'
    else:
        sigs = {IDENTIFIERS[role][i]: 'signature' for role, sig_count in action.sigs.items() for i in
                range(sig_count)}

    if action.endorser is not None:
        endorser_did = IDENTIFIERS[action.endorser][0]

    operation = randomOperation()
    req = Request(identifier=identifier,
                  operation=operation,
                  signature=sig,
                  signatures=sigs,
                  endorser=endorser_did)
    if action.amount is not None:
        setattr(req, PLUGIN_FIELD, action.amount)
    action = AuthActionAdd(txn_type=req.operation[TYPE],
                           field='some_field',
                           value='new_value',
                           is_owner=action.is_owner)

    return req, [action]


def validate(auth_constraint,
             valid_actions: List[Action],
             author, endorser, all_signatures, is_owner, amount,
             write_auth_req_validator,
             write_request_validation):
    set_auth_constraint(write_auth_req_validator,
                        auth_constraint)

    for signatures in all_signatures:
        next_action = Action(author=author, endorser=endorser, sigs=signatures,
                             is_owner=is_owner, amount=amount, extra_sigs=False)
        expected = is_expected(next_action, valid_actions)
        result = write_request_validation(*build_req_and_action(next_action))
        assert result == expected, \
            "Expected {} but result is {} for case {} and valid set {}".format(expected, result, next_action,
                                                                               valid_actions)


def is_expected(next_action: Action, valid_actions: List[Action]):
    for valid_action in valid_actions:
        if (next_action.author, next_action.endorser, next_action.is_owner, next_action.amount) != \
                (valid_action.author, valid_action.endorser, valid_action.is_owner, valid_action.amount):
            continue
        if not valid_action.extra_sigs and next_action.sigs != valid_action.sigs:
            continue
        if valid_action.extra_sigs and not (valid_action.sigs.items() <= next_action.sigs.items()):
            continue
        return True
    return False
