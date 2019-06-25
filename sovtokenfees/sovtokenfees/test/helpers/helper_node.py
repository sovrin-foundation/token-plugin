import copy

import sovtoken.test.helpers.helper_node as sovtoken_helper_node

from indy_common.constants import NYM
from sovtokenfees.req_handlers.batch_handlers.fee_batch_handler import DomainFeeBatchHandler
from sovtokenfees.req_handlers.read_handlers.get_fees_handler import GetFeesHandler
from sovtokenfees.req_handlers.write_handlers.domain_fee_handler import DomainFeeHandler

from common.serializers.serialization import domain_state_serializer

from indy_common.authorize.auth_actions import compile_action_id, ADD_PREFIX, EDIT_PREFIX

from indy_common.authorize.auth_cons_strategies import AbstractAuthStrategy
from sovtokenfees.constants import FEES_FIELD_NAME, GET_FEES
from sovtokenfees.domain import build_path_for_set_fees
from sovtokenfees.test.constants import txn_type_to_alias, alias_to_txn_type

from plenum.common.constants import DOMAIN_LEDGER_ID, CONFIG_LEDGER_ID


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
            deducted = req_handler._fees_tracker._deducted_fees.get(key, 0)
            assert deducted == amount

    def assert_set_fees_in_memory(self, fees):
        """ Assert nodes hold a certain fees in memory. """
        for node in self._nodes:
            req_handler = self._get_gfees_req_handler(node)
            assert req_handler.get_fees(is_committed=True, with_proof=True)[0] == fees

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

    def get_db_manager(self):
        return self._nodes[0].db_manager

    def get_write_req_validator(self):
        return self._nodes[0].write_req_validator

    def get_write_req_manager(self):
        return self._nodes[0].write_manager

    def _reset_fees(self, node):
        empty_fees = domain_state_serializer.serialize({})
        node.db_manager.get_state(CONFIG_LEDGER_ID).set(build_path_for_set_fees().encode(), empty_fees)

    def _get_fees_req_handler(self, node):
        return next(h for h in node.write_manager.request_handlers[NYM] if isinstance(h, DomainFeeHandler))

    def _get_gfees_req_handler(self, node):
        return node.read_manager.request_handlers[GET_FEES]

    @staticmethod
    def fill_auth_map_for_node(node, txn_type):
        validator = node.write_req_validator
        for rule_id, constraint in validator.auth_map.items():
            add_rule_id = compile_action_id(txn_type=txn_type, field='*', old_value='*', new_value='*',
                                            prefix=ADD_PREFIX)
            edit_rule_id = compile_action_id(txn_type=txn_type, field='*', old_value='*', new_value='*',
                                             prefix=EDIT_PREFIX)
            if AbstractAuthStrategy.is_accepted_action_id(add_rule_id, rule_id) or \
                    AbstractAuthStrategy.is_accepted_action_id(edit_rule_id, rule_id):
                constraint = copy.deepcopy(constraint)
                if constraint:
                    constraint.set_metadata({FEES_FIELD_NAME: txn_type_to_alias[txn_type]})
                    validator.auth_map[rule_id] = constraint

    def _fill_auth_map(self, txn_type):
        for node in self._nodes:
            self.fill_auth_map_for_node(node, txn_type)

    def set_fees_directly(self, fees):
        for fees_alias, fee in fees.items():
            txn_type = alias_to_txn_type[fees_alias]
            self._fill_auth_map(txn_type)
