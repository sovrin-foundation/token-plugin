import copy

import sovtoken.test.helpers.helper_node as sovtoken_helper_node
from plenum.common.constants import CONFIG_LEDGER_ID

from indy_common.authorize.auth_actions import compile_action_id, ADD_PREFIX, EDIT_PREFIX

from indy_common.authorize.auth_cons_strategies import AbstractAuthStrategy
from sovtokenfees.constants import FEES_FIELD_NAME
from sovtokenfees.domain import build_path_for_set_fees


class HelperNode(sovtoken_helper_node.HelperNode):
    """
    Extends the sovtoken HelperNode for fee functionality.

    # Methods
    - assert_deducted_fees
    - assert_set_fees_in_memory
    - fee_handler_can_pay_fees
    - get_fees_req_handler
    - reset_fees
    """

    def assert_deducted_fees(self, txn_type, seq_no, amount):
        """ Assert nodes have paid fees stored in memory """
        key = "{}#{}".format(txn_type, seq_no)
        for node in self._nodes:
            req_handler = self._get_fees_req_handler(node)
            deducted = req_handler.deducted_fees.get(key, 0)
            assert deducted == amount

    def assert_set_fees_in_memory(self, fees):
        """ Assert nodes hold a certain fees in memory. """
        for node in self._nodes:
            req_handler = self._get_fees_req_handler(node)
            assert req_handler.fees == fees

    def reset_fees(self):
        """ Reset the fees on each node. """
        for node in self._nodes:
            self._reset_fees(node)

    def fee_handler_can_pay_fees(self, request):
        """ Check the request can pay fees using a StaticFeeRequestHandler. """
        request_handler = self.get_fees_req_handler()
        return request_handler.can_pay_fees(request)

    def get_fees_req_handler(self):
        """ Get the fees request handler of the first node """
        return self._get_fees_req_handler(self._nodes[0])

    def _reset_fees(self, node):
        req_handler = self._get_fees_req_handler(node)
        empty_fees = req_handler.state_serializer.serialize({})
        req_handler.state.set(build_path_for_set_fees().encode(), empty_fees)

    def _get_fees_req_handler(self, node):
        return node.get_req_handler(ledger_id=CONFIG_LEDGER_ID)

    @staticmethod
    def fill_auth_map_for_node(node, txn_type):
        validator = node.write_req_validator
        keys = list()
        for rule_id, constraint in validator.auth_map.items():
            add_rule_id = compile_action_id(txn_type=txn_type, field='*', old_value='*', new_value='*',
                                            prefix=ADD_PREFIX)
            edit_rule_id = compile_action_id(txn_type=txn_type, field='*', old_value='*', new_value='*',
                                             prefix=EDIT_PREFIX)
            if AbstractAuthStrategy.is_accepted_action_id(add_rule_id,
                                                          rule_id) or AbstractAuthStrategy.is_accepted_action_id(
                    edit_rule_id, rule_id):
                constraint = copy.deepcopy(constraint)
                if constraint:
                    constraint.set_metadata({FEES_FIELD_NAME: txn_type})
                    validator.auth_map[rule_id] = constraint

    def _fill_auth_map(self, txn_type):
        for node in self._nodes:
            self.fill_auth_map_for_node(node, txn_type)

    def set_fees_directly(self, fees):
        for txn_type, fee in fees.items():
            self._fill_auth_map(txn_type)
