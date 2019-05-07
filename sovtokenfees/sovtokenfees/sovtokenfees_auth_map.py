from sovtokenfees.constants import SET_FEES
from indy_common.authorize.auth_actions import AuthActionEdit, AuthActionAdd
from indy_common.authorize.auth_constraints import ROLE, accepted_roles, AuthConstraint
from plenum.common.constants import TRUSTEE

add_fees = AuthActionAdd(txn_type=SET_FEES,
                         field="*",
                         value="*")

edit_fees = AuthActionEdit(txn_type=SET_FEES,
                           field="*",
                           old_value="*",
                           new_value="*")

# One Trustee constraint
one_trustee_constraint = AuthConstraint(TRUSTEE, 1)

sovtokenfees_auth_map = {
    add_fees.get_action_id(): one_trustee_constraint,
    edit_fees.get_action_id(): one_trustee_constraint,
}
