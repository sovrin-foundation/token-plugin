from indy_common.authorize.auth_actions import AbstractAuthAction
from indy_common.authorize.auth_constraints import AbstractAuthConstraint
from indy_common.authorize.authorizer import AbstractAuthorizer
from indy_common.types import Request


class FeesAuthorizer(AbstractAuthorizer):
    def __init__(self, fee_req_handler):
        super().__init__()
        self.fee_req_handler = fee_req_handler

    def authorize(self, request: Request, auth_constraint: AbstractAuthConstraint, auth_action: AbstractAuthAction) -> (
        bool, str):
        self.fee_req_handler.can_pay_fees(request, auth_action.get_action_id())
        return True, ''
