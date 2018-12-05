from plenum.common.constants import DOMAIN_LEDGER_ID
from sovtoken.constants import TOKEN_LEDGER_ID


class HelperNode():
    """
    Helper for dealing with the nodes.

    # Methods
    - get_last_ledger_transaction_on_nodes
    - get_token_req_handler
    """

    def __init__(self, nodes):
        self._nodes = nodes

    def get_last_ledger_transaction_on_nodes(self, ledger_id):
        """ Return last transaction stored on ledger from each node. """
        transactions = []
        for node in self._nodes:
            ledger = node.getLedger(ledger_id)
            last_sequence_number = ledger.size
            transactions.append(ledger.getBySeqNo(last_sequence_number))

        return transactions

    def get_token_req_handler(self):
        """ Get the token request handler of the first node. """
        return self._nodes[0].get_req_handler(ledger_id=TOKEN_LEDGER_ID)

    def get_domain_req_handler(self):
        """ Get the domain request handler of the first node. """
        return self._nodes[0].get_req_handler(ledger_id=DOMAIN_LEDGER_ID)
