import json

from sovtokenfees.constants import SET_FEES, FEES
from sovtokenfees.test.constants import NYM_FEES_ALIAS

from plenum.common.constants import TXN_TYPE


def steward_do_set_fees(helpers, fees):
    """ Sends and check a set_fees txn """
    payload = {
        TXN_TYPE: SET_FEES,
        FEES: fees,
    }

    request = helpers.request._create_request(payload,
                                              identifier=helpers.wallet._stewards[0])
    request = helpers.wallet.sign_request_stewards(json.dumps(request.as_dict), number_signers=1)
    helpers.sdk.sdk_send_and_check([request])


def set_fees(helpers, fees, trustee=True):
    new_fees = dict(fees)
    new_fees[NYM_FEES_ALIAS] += 1
    if trustee:
        helpers.general.do_set_fees(new_fees)
    else:
        steward_do_set_fees(helpers, new_fees)
    get_fees = helpers.general.do_get_fees()
    assert new_fees == get_fees.get("fees")


def add_fees_request_with_address(helpers, fee_amount, request, address):
    if fee_amount is None:
        return request
    utxos_found = helpers.general.get_utxo_addresses([address])[0]
    request_with_fees = helpers.request.add_fees(
        request,
        utxos_found,
        fee_amount,
        change_address=address
    )[0]
    request_with_fees = json.loads(request_with_fees)
    setattr(request, FEES, request_with_fees[FEES])
    return request
