import sovtoken.test.helpers.helper_node as sovtoken_helper_node
from plenum.common.constants import CONFIG_LEDGER_ID


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
        return request_handler.can_pay_fees(request, None)

    def get_fees_req_handler(self):
        """ Get the fees request handler of the first node """
        return self._get_fees_req_handler(self._nodes[0])

    def _reset_fees(self, node):
        req_handler = self._get_fees_req_handler(node)
        empty_fees = req_handler.state_serializer.serialize({})
        req_handler.state.set(req_handler.fees_state_key, empty_fees)
        # req_handler.fees = {}

    def _get_fees_req_handler(self, node):
        return node.get_req_handler(ledger_id=CONFIG_LEDGER_ID)
