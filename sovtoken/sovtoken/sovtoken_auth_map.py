from collections import OrderedDict

from sovtoken.constants import MINT_PUBLIC, XFER_PUBLIC
from indy_common.authorize.auth_actions import AuthActionEdit, AuthActionAdd
from indy_common.authorize.auth_constraints import ROLE, accepted_roles, AuthConstraint
from plenum.common.constants import TRUSTEE

add_mint = AuthActionAdd(txn_type=MINT_PUBLIC,
                         field="*",
                         value="*")

add_xfer = AuthActionAdd(txn_type=XFER_PUBLIC,
                         field="*",
                         value="*")

# Anyone constraint
anyone_constraint = AuthConstraint(role='*',
                                   sig_count=0)

# Three Trustee constraint
three_trustee_constraint = AuthConstraint(TRUSTEE, 3)

sovtoken_auth_map = OrderedDict([
    (add_mint.get_action_id(), three_trustee_constraint),
    (add_xfer.get_action_id(), anyone_constraint),
])
