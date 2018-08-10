from plenum.common.constants import CONFIG_LEDGER_ID


class HelperNode():
    """
    Helper for dealing with the nodes.

    # Methods
    - assert_deducted_fees
    - assert_set_fees_in_memory
    - get_last_ledger_transaction_on_nodes
    - reset_fees
    """

    def __init__(self, nodes):
        self._nodes = nodes

    def assert_deducted_fees(self, txn_type, seq_no, amount):
        """ Assert nodes have paid fees stored in memory """
        key = "{}#{}".format(txn_type, seq_no)
        for node in self._nodes:
            req_handler = self._get_fees_req_handler(node)
            print(req_handler.deducted_fees)
            deducted = req_handler.deducted_fees.get(key, 0)
            print("{} : {}".format(key, deducted))
            assert deducted == amount

    def assert_set_fees_in_memory(self, fees):
        """ Assert nodes hold a certain fees in memory. """
        for node in self._nodes:
            req_handler = self._get_fees_req_handler(node)
            assert req_handler.fees == fees

    def get_last_ledger_transaction_on_nodes(self, ledger_id):
        """ Return last transaction stored on ledger from each node. """
        transactions = []
        for node in self._nodes:
            ledger = node.getLedger(ledger_id)
            last_sequence_number = ledger.size
            transactions.append(ledger.getBySeqNo(last_sequence_number))

        return transactions

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
