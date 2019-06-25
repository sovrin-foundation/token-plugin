from sovtokenfees.req_handlers.write_handlers.auth_rule_fee_handler import AuthRuleFeeHandler

from plenum.server.database_manager import DatabaseManager
from plenum.common.request import Request

from indy_node.server.request_handlers.config_req_handlers.auth_rule.auth_rules_handler import AuthRulesHandler
from indy_common.authorize.auth_request_validator import WriteRequestValidator


class AuthRulesFeeHandler(AuthRulesHandler):

    def __init__(self, database_manager: DatabaseManager, write_req_validator: WriteRequestValidator,
                 get_fees_handler):
        super().__init__(database_manager, write_req_validator)
        self._get_fees_handler = get_fees_handler

    def dynamic_validation(self, request: Request):
        super().dynamic_validation(request)
        AuthRuleFeeHandler.fees_specific_validation(self._get_fees_handler, request)
