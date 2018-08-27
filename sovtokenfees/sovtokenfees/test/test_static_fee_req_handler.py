import pytest

from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler
from plenum.common.constants import DOMAIN_LEDGER_ID, CONFIG_LEDGER_ID
from plenum.common.constants import NYM
from sovtokenfees.constants import FEES
from sovtoken.constants import XFER_PUBLIC, TOKEN_LEDGER_ID, ADDRESS, AMOUNT, SEQNO
from sovtoken.exceptions import InvalidFundsError
from plenum.common.exceptions import UnauthorizedClientRequest, InvalidClientRequest


VALID_FEES = {XFER_PUBLIC: 8, NYM: 10}


@pytest.fixture
def token_handler_a(helpers):
    return helpers.node.get_fees_req_handler()


@pytest.fixture(scope="function", autouse=True)
def reset_token_handler(token_handler_a):
    old_head = token_handler_a.state.committedHead
    yield
    token_handler_a.state.revertToHead(old_head)
    token_handler_a.onBatchRejected()


def test_non_existent_input_xfer(helpers):
    """
    Expect an InvalidFundsError on a xfer request with inputs which don't
    contain a valid utxo.
    """

    helpers.general.do_set_fees(VALID_FEES)

    [
        address1,
        address2
    ] = helpers.wallet.create_new_addresses(2)

    inputs = [{ADDRESS: address1, SEQNO: 1}]
    outputs = [{ADDRESS: address2, AMOUNT: 290}]

    request = helpers.request.transfer(inputs, outputs)

    with pytest.raises(InvalidFundsError) as e:
        helpers.node.fee_handler_can_pay_fees(request)


def test_non_existent_input_non_xfer(helpers):
    """
    Expect an InvalidFundsError on a nym request with inputs which don't
    contain a valid utxo.
    """
    helpers.general.do_set_fees(VALID_FEES)

    utxos = [{
        ADDRESS: helpers.wallet.create_address(),
        SEQNO: 1,
        AMOUNT: 10
    }]

    request = helpers.request.nym()
    request = helpers.request.add_fees(request, utxos, 10)

    with pytest.raises(InvalidFundsError) as e:
        try:
            helpers.node.fee_handler_can_pay_fees(request)
        except Exception as ex:
            print("*****************"+str(ex))
            raise ex


# Method returns None if it was successful -
# TODO: Refactoring should be looked at to return a boolean
# Instead of assuming that everything is good when the return value is None.
# - Static Fee Request Handler (doStaticValidation)
def test_static_fee_req_handler_do_static_validation_valid(
    helpers,
    token_handler_a,
):
    request = helpers.request.set_fees(VALID_FEES)

    ret_value = token_handler_a.doStaticValidation(request)
    assert ret_value is None


# - Static Fee Request Handler (doStaticValidation)
def test_static_fee_req_handler_do_static_validation_invalid(
    helpers,
    token_handler_a,
):
    request = helpers.request.set_fees(VALID_FEES)
    request.operation.pop(FEES)

    with pytest.raises(InvalidClientRequest):
        token_handler_a.doStaticValidation(request)


# - Static Fee Request Handler (validate)
def test_static_fee_req_handler_validate_invalid_signee(
    helpers,
    token_handler_a,
):
    request = helpers.request.set_fees(VALID_FEES)
    (did, sig) = request.signatures.popitem()
    reversed_did = did[::-1]
    request.signatures[reversed_did] = sig

    with pytest.raises(UnauthorizedClientRequest):
        token_handler_a.validate(request)


# - Static Fee Request Handler (validate)
def test_static_fee_req_handler_validate_invalid_missing_signee(
    helpers,
    token_handler_a,
):
    request = helpers.request.set_fees(VALID_FEES)
    (did, sig) = request.signatures.popitem()

    with pytest.raises(UnauthorizedClientRequest):
        token_handler_a.validate(request)


# - Static Fee Request Handler (validate)
def test_static_fee_req_handler_validate_valid_extra_signee(
    helpers,
    token_handler_a,
    increased_trustees
):
    request = helpers.request.set_fees(VALID_FEES)
    request.signatures = None
    request = helpers.wallet.sign_request(request, increased_trustees)
    assert len(request.signatures) == 7

    valid = token_handler_a.validate(request)

    assert valid is None


# - Static Fee Request Handler (apply)
def test_static_fee_req_handler_apply(helpers, token_handler_a):
    request = helpers.request.set_fees(VALID_FEES)

    prev_size = token_handler_a.ledger.uncommitted_size
    ret_value = token_handler_a.apply(request, 10)
    assert ret_value[0] == prev_size + 1
