from sovtokenfees.constants import SET_FEES
from indy_common.authorize.auth_actions import AuthActionEdit
from indy_common.authorize.auth_constraints import ROLE, accepted_roles, AuthConstraint
from plenum.common.constants import TRUSTEE

edit_fees = AuthActionEdit(txn_type=SET_FEES,
                           field="*",
                           old_value="*",
                           new_value="*")

# Three Trustee constraint
three_trustee_constraint = AuthConstraint(TRUSTEE, 3)

sovtokenfees_auth_map = {
    edit_fees.get_action_id(): three_trustee_constraint,
}
