from indy_common.authorize.authorizer import AbstractAuthorizer

from indy_common.authorize.auth_constraints import AuthConstraint

from indy_common.authorize.auth_actions import AbstractAuthAction
from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler
from stp_core.common.log import getlogger

from plenum.common.exceptions import UnauthorizedClientRequest


logger = getlogger()

FEES_FIELD_NAME = 'fees'


class FeesAuthorizer(AbstractAuthorizer):
    def __init__(self, fees_req_handler: StaticFeesReqHandler):
        super().__init__()
        self.fees_req_handler = fees_req_handler

    def _get_fees_from_constraint(self, auth_constaint: AuthConstraint):
        if auth_constaint.metadata:
            if FEES_FIELD_NAME in auth_constaint.metadata:
                return auth_constaint.metadata[FEES_FIELD_NAME]

    def _can_pay_fees(self, request, required_fees):
        try:
            self.fees_req_handler.can_pay_fees(request, required_fees)
        except Exception as e:
            logger.warning("Encountered exception while can_pay_fees validation: {}".format(e))
            return False
        return True

    def authorize(self,
                  request,
                  auth_constraint: AuthConstraint,
                  auth_action: AbstractAuthAction=None):
        constraint_fees = self._get_fees_from_constraint(auth_constraint)
        is_fees_required = True if constraint_fees else False
        if is_fees_required and not self.fees_req_handler.has_fees(request):
            logger.warning("Validation error: Fees are required for this txn type")
            raise UnauthorizedClientRequest(request.identifier,
                                            request.reqId,
                                            "Fees are required for this txn type")
        if not is_fees_required and self.fees_req_handler.has_fees(request):
            logger.warning("Validation error: Fees are not required for this txn type")
            raise UnauthorizedClientRequest(request.identifier,
                                            request.reqId,
                                            "Fees are not required for this txn type")
        if not is_fees_required and not self.fees_req_handler.has_fees(request):
            return True, ""
        if not self._can_pay_fees(request, constraint_fees):
            logger.warning("Validation error: Cannot pay fees")
            raise UnauthorizedClientRequest(request.identifier,
                                            request.reqId,
                                            "Cannot pay fees")
        return True, ""
