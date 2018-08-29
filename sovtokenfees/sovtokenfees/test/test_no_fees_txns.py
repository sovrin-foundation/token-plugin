import json

from plenum.common.constants import NYM
from plenum.common.txn_util import get_seq_no
from sovtoken.constants import XFER_PUBLIC
from sovtokenfees.constants import FEES


TXN_FEES = {
    NYM: 0,
    XFER_PUBLIC: 8
}


def test_txn_with_no_fees_specified(helpers):
    helpers.general.do_set_fees(TXN_FEES)
    request = helpers.request.nym()
    helpers.sdk.send_and_check_request_objects([request])
