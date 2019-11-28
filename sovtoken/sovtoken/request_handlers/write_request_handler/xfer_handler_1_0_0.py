from sovtoken.exceptions import UTXOError

from sovtoken.constants import INPUTS, OUTPUTS
from sovtoken.request_handlers.token_utils import TokenStaticHelper
from sovtoken.request_handlers.write_request_handler.xfer_handler import XferHandler
from sovtoken.types import Output

from plenum.common.exceptions import InvalidClientMessageException, InvalidClientRequest, OperationError
from plenum.common.txn_util import get_payload_data, get_seq_no, add_sigs_to_txn


class XferHandler100(XferHandler):

    def update_state(self, txn, prev_result, request, is_committed=False):
        try:
            payload = get_payload_data(txn)
            for inp in payload[INPUTS]:
                TokenStaticHelper.spend_input(
                    self.state,
                    self.utxo_cache,
                    inp["address"],
                    inp["seqNo"],
                    is_committed=is_committed,
                    remove_spent=False)
            for output in payload[OUTPUTS]:
                seq_no = get_seq_no(txn)
                TokenStaticHelper.add_new_output(
                    self.state,
                    self.utxo_cache,
                    Output(output["address"],
                           seq_no,
                           output["amount"]),
                    is_committed=is_committed)
        except UTXOError as ex:
            error = 'Exception {} while updating state'.format(ex)
            raise OperationError(error)
