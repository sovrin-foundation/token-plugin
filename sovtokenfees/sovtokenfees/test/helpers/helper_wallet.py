from plenum.common.txn_util import get_payload_data, get_seq_no

from sovtoken.constants import INPUTS, OUTPUTS
from sovtoken.test.helpers.helper_wallet import HelperWallet as _HelperWallet

from sovtokenfees.constants import FEES


class HelperWallet(_HelperWallet):

    def handle_txn_with_fees(self, response):
        fees_response = response[FEES]
        data = get_payload_data(fees_response)
        seq_no = get_seq_no(fees_response)
        self._update_inputs(data[INPUTS])
        self._update_outputs(data[OUTPUTS], seq_no)
