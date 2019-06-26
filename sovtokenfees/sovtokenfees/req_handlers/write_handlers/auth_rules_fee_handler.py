from indy_common.constants import AUTH_RULES, RULES

from indy_node.server.request_handlers.config_req_handlers.auth_rule.static_auth_rule_helper import StaticAuthRuleHelper
from plenum.common.exceptions import InvalidClientMessageException

from plenum.common.constants import CONFIG_LEDGER_ID

from plenum.server.request_handlers.handler_interfaces.write_request_handler import WriteRequestHandler
from sovtokenfees.req_handlers.write_handlers.auth_rule_fee_handler import AuthRuleFeeHandler

from plenum.server.database_manager import DatabaseManager
from plenum.common.request import Request

from indy_common.authorize.auth_request_validator import WriteRequestValidator


class AuthRulesFeeHandler(WriteRequestHandler):

    def __init__(self, database_manager: DatabaseManager, get_fees_handler):
        super().__init__(database_manager, AUTH_RULES, CONFIG_LEDGER_ID)
        self._get_fees_handler = get_fees_handler

    def static_validation(self, request: Request):
        pass

    def dynamic_validation(self, request: Request):
        self.fees_specific_validation(request)

    def update_state(self, txn, prev_result, request, is_committed=False):
        pass

    def apply_request(self, request: Request, batch_ts, prev_result):
        return None, None, None

    def fees_specific_validation(self, request: Request):
        operation = request.operation
        current_fees = self._get_fees_handler.get_fees()
        constraints = []
        for rule in operation[RULES]:
            constraints.append(StaticAuthRuleHelper.get_auth_constraint(rule))

        for constraint in constraints:
            wrong_aliases = []
            AuthRuleFeeHandler.validate_metadata(current_fees, constraint, wrong_aliases)
            if len(wrong_aliases) > 0:
                raise InvalidClientMessageException(request.identifier,
                                                    request.reqId,
                                                    "Fees alias(es) {} does not exist in current fees {}. "
                                                    "Please add the alias(es) via SET_FEES transaction first.".
                                                    format(", ".join(wrong_aliases),
                                                           current_fees))
