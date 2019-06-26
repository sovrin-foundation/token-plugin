from indy_common.authorize.auth_constraints import AuthConstraint, ConstraintsEnum
from indy_common.authorize.auth_request_validator import WriteRequestValidator
from indy_node.server.request_handlers.config_req_handlers.auth_rule.static_auth_rule_helper import StaticAuthRuleHelper

from indy_node.server.request_handlers.config_req_handlers.auth_rule.auth_rule_handler import AuthRuleHandler
from plenum.server.database_manager import DatabaseManager

from plenum.common.exceptions import InvalidClientMessageException
from plenum.common.request import Request
from sovtokenfees.constants import FEES_FIELD_NAME


class AuthRuleFeeHandler(AuthRuleHandler):

    def __init__(self, database_manager: DatabaseManager, write_req_validator: WriteRequestValidator,
                 get_fees_handler):
        super().__init__(database_manager, write_req_validator)
        self._get_fees_handler = get_fees_handler

    def dynamic_validation(self, request: Request):
        super().dynamic_validation(request)
        self.fees_specific_validation(self._get_fees_handler, request)

    @staticmethod
    def fees_specific_validation(get_fees_handler, request: Request):
        operation = request.operation
        current_fees = get_fees_handler.get_fees()
        constraint = StaticAuthRuleHelper.get_auth_constraint(operation)
        wrong_aliases = []
        AuthRuleFeeHandler.validate_metadata(get_fees_handler.get_fees(), constraint, wrong_aliases)
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
