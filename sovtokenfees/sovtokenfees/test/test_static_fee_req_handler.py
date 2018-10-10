import pytest

from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler
from plenum.common.constants import DOMAIN_LEDGER_ID, CONFIG_LEDGER_ID, TXN_TYPE
from plenum.common.constants import NYM
from sovtokenfees.constants import FEES, SET_FEES
from sovtoken.constants import XFER_PUBLIC, TOKEN_LEDGER_ID, ADDRESS, AMOUNT, SEQNO
from sovtoken.exceptions import InvalidFundsError
from plenum.common.exceptions import UnauthorizedClientRequest, InvalidClientRequest


VALID_FEES = {
    NYM: 1,
    "100": 1,
    "101": 1,
    "102": 1,
    "113": 1,
    "114": 1,
    XFER_PUBLIC: 1
}


@pytest.fixture
def fee_handler(helpers):
    return helpers.node.get_fees_req_handler()


@pytest.fixture(scope="function", autouse=True)
def reset_token_handler(fee_handler):
    old_head = fee_handler.state.committedHead
    yield
    fee_handler.state.revertToHead(old_head)
    fee_handler.onBatchRejected()


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

    with pytest.raises(InvalidFundsError):
        helpers.node.fee_handler_can_pay_fees(request)


class TestStaticValidation:
    # Method returns None if it was successful -
    # TODO: Refactoring should be looked at to return a boolean
    # Instead of assuming that everything is good when the return value is None.
    # - Static Fee Request Handler (doStaticValidation)
    def test_set_fees_valid_txn_types(self, helpers, fee_handler):
        """
        StaticValidation of a set fees request with all of the whitelisted txn
        types.
        """

        request = helpers.request.set_fees(VALID_FEES)

        result = fee_handler.doStaticValidation(request)

        assert result is None

    def test_set_fees_invalid_txn_types(self, helpers, fee_handler):
        """
        StaticValidation of a set fees request that contains a txn type that
        is not whitelisted.
        """

        fees = {SET_FEES: 1}

        request = helpers.request.set_fees(fees)

        with pytest.raises(InvalidClientRequest, match="set_fees -- Fees are not allowed for txn ") as e:
            fee_handler.doStaticValidation(request)
            assert e.contain()

    def test_set_fees_missing_fees(self, helpers, fee_handler):
        """
        StaticValidation of a set fees request where 'fees' is not a dict.
        """

        request = helpers.request.set_fees(VALID_FEES)
        request.operation.pop(FEES)

        with pytest.raises(InvalidClientRequest, match="expected types 'dict', got"):
            fee_handler.doStaticValidation(request)

    def test_get_fees(self, helpers, fee_handler):
        """
        StaticValidation of a get fees request does nothing.
        """

        request = helpers.request.get_fees()
        fee_handler.doStaticValidation(request)

    def test_unkown_type(self, helpers, fee_handler):
        """
        StaticValidation of an unknown request does nothing.
        """

        payload = {TXN_TYPE: '300'}
        request = helpers.request._create_request(payload)
        fee_handler.doStaticValidation(request)


class TestValidation():
    def test_set_fees_invalid_signee(self, helpers, fee_handler):
        """
        Validation of a set_fees request where one of the signees doesn't
        exist.
        """

        request = helpers.request.set_fees(VALID_FEES)
        (did, sig) = request.signatures.popitem()
        reversed_did = did[::-1]
        request.signatures[reversed_did] = sig

        with pytest.raises(UnauthorizedClientRequest):
            fee_handler.validate(request)

    def test_set_fees_invalid_signature(self, helpers, fee_handler):
        """
        Validation of a set_fees request with an invalid signatures still
        passes.

        An invalid signature is expected to be caught with
        FeesAuthNr.authenticate and isn't checked here.
        """

        request = helpers.request.set_fees(VALID_FEES)
        (did, sig) = request.signatures.popitem()
        reversed_sig = sig[::-1]
        request.signatures[did] = reversed_sig

        fee_handler.validate(request)

    def test_set_fees_test_missing_signee(self, helpers, fee_handler):
        """
        Validation of a set_fees request without the minimum number of
        trustees.
        """

        request = helpers.request.set_fees(VALID_FEES)
        (did, sig) = request.signatures.popitem()

        with pytest.raises(UnauthorizedClientRequest):
            fee_handler.validate(request)

    def test_set_fees_test_extra_signees(
        self,
        helpers,
        fee_handler,
        increased_trustees
    ):
        """
        Validation of a set_fees request passes with extra signees.
        """

        request = helpers.request.set_fees(VALID_FEES)
        request.signatures = None
        request = helpers.wallet.sign_request(request, increased_trustees)
        assert len(request.signatures) == 7

        valid = fee_handler.validate(request)

        assert valid is None

    def test_get_fees_invalid_identifier(self, helpers, fee_handler):
        """
        Validation of a get_fees request does nothing.
        """

        request = helpers.request.get_fees()
        request._identifier = None
        fee_handler.validate(request)

    def test_validate_unknown_type(self, helpers, fee_handler):
        """
        Validation of a non-fees request passes.
        """

        request = helpers.request.nym()
        fee_handler.validate(request)

# - Static Fee Request Handler (apply)
def test_static_fee_req_handler_apply(helpers, fee_handler):
    request = helpers.request.set_fees(VALID_FEES)

    prev_size = fee_handler.ledger.uncommitted_size
    ret_value = fee_handler.apply(request, 10)
    assert ret_value[0] == prev_size + 1
