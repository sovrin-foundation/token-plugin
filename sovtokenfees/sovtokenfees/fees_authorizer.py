from indy_common.authorize.authorizer import AbstractAuthorizer

from indy_common.authorize.auth_constraints import AuthConstraint

from indy_common.authorize.auth_actions import AbstractAuthAction
from sovtoken.constants import XFER_PUBLIC
from sovtokenfees.constants import FEES_FIELD_NAME
from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler
from stp_core.common.log import getlogger

from plenum.common.exceptions import UnauthorizedClientRequest

from state.pruning_state import PruningState

logger = getlogger()


class FeesAuthorizer(AbstractAuthorizer):
    def __init__(self, fees_req_handler: StaticFeesReqHandler, config_state: PruningState):
        super().__init__()
        self.fees_req_handler = fees_req_handler
        self.config_state = config_state
        self.state_serializer = StaticFeesReqHandler.state_serializer

    def _get_fees_alias_from_constraint(self, auth_constaint: AuthConstraint):
        if auth_constaint.metadata:
            if FEES_FIELD_NAME in auth_constaint.metadata:
                return auth_constaint.metadata[FEES_FIELD_NAME]

    def _can_pay_fees(self, request, required_fees):
        self.fees_req_handler.can_pay_fees(request, required_fees)

    def _get_fees_from_state(self):
        key = StaticFeesReqHandler.build_path_for_set_fees()
        serz = self.config_state.get(key,
                                     isCommitted=False)
        if not serz:
            return {}
        return self.state_serializer.deserialize(serz)

    def authorize(self,
                  request,
                  auth_constraint: AuthConstraint,
                  auth_action: AbstractAuthAction=None):
        fees_alias = self._get_fees_alias_from_constraint(auth_constraint)
        fees = self._get_fees_from_state()
        fees_amount = fees.get(fees_alias, 0)
        is_fees_required = True if fees_amount else False
        if request.txn_type != XFER_PUBLIC:
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
        self._can_pay_fees(request, fees_amount)
        return True, ""
