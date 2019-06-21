from indy_common.constants import NYM, AUTH_RULE
from plenum.common.constants import DOMAIN_LEDGER_ID, CONFIG_LEDGER_ID
from sovtoken.constants import TOKEN_LEDGER_ID, XFER_PUBLIC, GET_UTXO, MINT_PUBLIC


class HelperNode():
    """
    Helper for dealing with the nodes.

    # Methods
    - get_last_ledger_transaction_on_nodes
    - get_token_req_handler
    """

    def __init__(self, nodes):
        self._nodes = nodes

    def get_primary_node(self):
        for n in self._nodes:
            if n.master_replica.isPrimary:
                return n

    def get_last_ledger_transaction_on_nodes(self, ledger_id):
        """ Return last transaction stored on ledger from each node. """
        transactions = []
        for node in self._nodes:
            ledger = node.getLedger(ledger_id)
            last_sequence_number = ledger.size
            transactions.append(ledger.getBySeqNo(last_sequence_number))

        return transactions

    @property
    def xfer_handler(self):
        """ Get the xfer request handler of the first node. """
        return self._nodes[0].write_manager.request_handlers[XFER_PUBLIC][0]

    @property
    def mint_handler(self):
        """ Get the xfer request handler of the first node. """
        return self._nodes[0].write_manager.request_handlers[MINT_PUBLIC][0]

    @property
    def nym_handler(self):
        """ Get the NYM request handler of the first node. """
        return self._nodes[0].write_manager.request_handlers[NYM][0]

    @property
    def get_utxo_handler(self):
        return self._nodes[0].read_manager.request_handlers[GET_UTXO]
