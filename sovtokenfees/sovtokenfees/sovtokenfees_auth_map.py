from typing import Dict

from sovtoken.constants import MINT_PUBLIC, XFER_PUBLIC
from sovtokenfees.constants import FEES, SET_FEES

from indy_common.authorize.auth_actions import AuthActionEdit, AuthActionAdd

from indy_common.constants import NYM

from indy_common.authorize.auth_constraints import ROLE, accepted_roles, AuthConstraint
from plenum.common.constants import TRUSTEE, STEWARD, VERKEY

edit_role_actions = {}  # type: Dict[str, Dict[str, AuthActionEdit]]
for role_from in accepted_roles:
    edit_role_actions[role_from] = {}
    for role_to in accepted_roles:
        edit_role_actions[role_from][role_to] = AuthActionEdit(txn_type=NYM,
                                                               field=ROLE,
                                                               old_value=role_from,
                                                               new_value=role_to)

edit_fees = AuthActionEdit(txn_type=SET_FEES,
                           field="*",
                           old_value="*",
                           new_value="*")

add_mint = AuthActionAdd(txn_type=MINT_PUBLIC,
                         field="*",
                         value="*")

add_xfer = AuthActionAdd(txn_type=XFER_PUBLIC,
                         field="*",
                         value="*")

# Anyone constraint
anyone_constraint = AuthConstraint(role='*',
                                   sig_count=1)

# One Trustee constraint
one_trustee_constraint = AuthConstraint(TRUSTEE, 1)

# Three Trustee constraint
three_trustee_constraint = AuthConstraint(TRUSTEE, 3)

sovtokenfees_auth_map = {
    edit_fees.get_action_id(): one_trustee_constraint,
    add_mint.get_action_id(): three_trustee_constraint,
    add_xfer.get_action_id(): anyone_constraint,
}
