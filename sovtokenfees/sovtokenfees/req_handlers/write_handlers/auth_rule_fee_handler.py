from typing import Optional

from indy_common.authorize.auth_constraints import AuthConstraint, ConstraintsEnum
from indy_common.constants import AUTH_RULE
from indy_node.server.request_handlers.config_req_handlers.auth_rule.static_auth_rule_helper import StaticAuthRuleHelper
from sovtokenfees.constants import FEES_FIELD_NAME

from plenum.common.constants import CONFIG_LEDGER_ID
from plenum.common.exceptions import InvalidClientMessageException
from plenum.common.request import Request
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.handler_interfaces.write_request_handler import WriteRequestHandler


class AuthRuleFeeHandler(WriteRequestHandler):

    def __init__(self, database_manager: DatabaseManager, get_fees_handler):
        super().__init__(database_manager, AUTH_RULE, CONFIG_LEDGER_ID)
        self._get_fees_handler = get_fees_handler

    def static_validation(self, request: Request):
        pass

    def dynamic_validation(self, request: Request, req_pp_time: Optional[int]):
        self.fees_specific_validation(request)

    def additional_dynamic_validation(self, request, req_pp_time: Optional[int]):
        pass

    def update_state(self, txn, prev_result, request, is_committed=False):
        pass

    def apply_request(self, request: Request, batch_ts, prev_result):
        return None, None, None

    def fees_specific_validation(self, request: Request):
        operation = request.operation
        current_fees = self._get_fees_handler.get_fees()
        constraint = StaticAuthRuleHelper.get_auth_constraint(operation)
        wrong_aliases = []
        AuthRuleFeeHandler.validate_metadata(current_fees, constraint, wrong_aliases)
        if len(wrong_aliases) > 0:
            raise InvalidClientMessageException(request.identifier,
                                                request.reqId,
                                                "Fees alias(es) {} does not exist in current fees {}. "
                                                "Please add the alias(es) via SET_FEES transaction first.".
                                                format(", ".join(wrong_aliases),
                                                       current_fees))

    @staticmethod
    def validate_metadata(current_fees, constraint: AuthConstraint, wrong_aliases):
        if constraint.constraint_id == ConstraintsEnum.FORBIDDEN_CONSTRAINT_ID:
            return
        if constraint.constraint_id != ConstraintsEnum.ROLE_CONSTRAINT_ID:
            for constr in constraint.auth_constraints:
                AuthRuleFeeHandler.validate_metadata(current_fees, constr, wrong_aliases)
        else:
            meta_alias = constraint.metadata.get(FEES_FIELD_NAME, None)
            if meta_alias and meta_alias not in current_fees:
                wrong_aliases.append(meta_alias)
