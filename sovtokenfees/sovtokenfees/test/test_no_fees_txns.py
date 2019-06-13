from sovtokenfees.test.constants import NYM_FEES_ALIAS, XFER_PUBLIC_FEES_ALIAS

TXN_FEES = {
    NYM_FEES_ALIAS: 0,
    XFER_PUBLIC_FEES_ALIAS: 8
}


def test_txn_with_no_fees_specified(helpers):
    helpers.general.do_set_fees(TXN_FEES)
    request = helpers.request.nym()
    helpers.sdk.send_and_check_request_objects([request])
