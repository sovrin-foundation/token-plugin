import json

from plenum.common.constants import NYM
from plenum.common.txn_util import get_seq_no
from sovtoken.constants import XFER_PUBLIC, ADDRESS, AMOUNT, SEQNO
from sovtokenfees.constants import FEES


TXN_FEES = {
    NYM: 0,
    XFER_PUBLIC: 8
}


def test_txn_with_no_fees_specified(helpers):
    helpers.general.do_set_fees(TXN_FEES)
    request = helpers.request.nym()
    helpers.sdk.send_and_check_request_objects([request])


def test_txn_with_0_fees_specified(helpers):
    helpers.general.do_set_fees(TXN_FEES)
    address = helpers.wallet.create_address()
    outputs = [{ADDRESS: address, AMOUNT: 1000}]
    helpers.general.do_mint(outputs)
    utxos = helpers.general.get_utxo_addresses([address])[0]

    request = helpers.request.nym()
    helpers.request.add_fees(
        request,
        utxos,
        fee_amount=0,
        change_address=address
    )
    responses = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(responses)
    fee_seq_no = get_seq_no(result[FEES])

    utxos = helpers.general.get_utxo_addresses([address])[0]

    assert utxos == [{
        ADDRESS: address,
        SEQNO: fee_seq_no,
        AMOUNT: 1000
    }]
