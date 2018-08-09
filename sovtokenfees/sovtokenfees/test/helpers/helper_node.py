from plenum.common.constants import CONFIG_LEDGER_ID


class HelperNode():
    """
    Helper for dealing with the nodes.

    # Methods
    - check_fees_in_memory_map
    - reset_fees
    """

    def __init__(self, nodes):
        self._nodes = nodes

    def check_fees_in_memory_map(self, fees):
        """ Assert nodes hold a certain fees in memory. """
        for node in self._nodes:
            req_handler = self._get_fees_req_handler(node)
            assert req_handler.fees == fees

    def reset_fees(self):
        """ Reset the fees on each node. """
        for node in self._nodes:
            self._reset_fees(node)

    def _reset_fees(self, node):
        req_handler = self._get_fees_req_handler(node)
        empty_fees = req_handler.state_serializer.serialize({})
        req_handler.state.set(req_handler.fees_state_key, empty_fees)
        req_handler.fees = {}

    def _get_fees_req_handler(self, node):
        return node.get_req_handler(ledger_id=CONFIG_LEDGER_ID)
