import math
from collections import OrderedDict

import base58
import pytest
from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no

from plenum.common.constants import (IDENTIFIER, STATE_PROOF,
                                     TXN_PAYLOAD_METADATA_REQ_ID, TXN_TYPE)
from plenum.common.exceptions import (InvalidClientMessageException,
                                      InvalidClientRequest, OperationError,
                                      UnauthorizedClientRequest)
from plenum.common.txn_util import (append_txn_metadata, get_from,
                                    get_payload_data, get_req_id, reqToTxn)
from sovtoken.constants import (ADDRESS, GET_UTXO, INPUTS, MINT_PUBLIC,
                                OUTPUTS, TOKEN_LEDGER_ID)
from sovtoken.exceptions import ExtraFundsError, InsufficientFundsError, TokenValueError
from sovtoken.test.txn_response import TxnResponse, get_sorted_signatures
from sovtoken.token_req_handler import TokenReqHandler
from sovtoken.types import Output

# Test Constants
VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"
CONS_TIME = 1518541344


@pytest.fixture
def token_handler_a(helpers):
    h = helpers.node.get_token_req_handler()
    old_head = h.state.committedHead
    yield h
    h.state.revertToHead(old_head)
    # TODO: this is a function fixture. Do we need this revert there?
    # h.onBatchRejected()


@pytest.fixture
def token_handler_b(nodeSet):
    h = nodeSet[1].ledger_to_req_handler[TOKEN_LEDGER_ID]
    old_head = h.state.committedHead
    yield h
    h.state.revertToHead(old_head)
    # TODO: this is a function fixture. Do we need this revert there?
    # h.onBatchRejected()


@pytest.fixture(scope="module")
def addresses(helpers):
    addresses = helpers.wallet.create_new_addresses(2)
    outputs = [{"address": addresses[0], "amount": 40}, {"address": addresses[1], "amount": 60}]
    helpers.general.do_mint(outputs)
    return addresses

@pytest.fixture(scope="module")
def addresses_inner(helpers):
    addresses = [helpers.wallet.create_address_inner() for _ in [1, 2]]
    outputs = [{"address": "pay:sov:" + addresses[0], "amount": 40}, {"address": "pay:sov:" + addresses[1], "amount": 60}]
    helpers.general.do_mint(outputs)
    return addresses


def test_token_req_handler_commit_batch_different_state_root(
        token_handler_a
):
    with pytest.raises(TokenValueError):
        token_handler_a._commit_to_utxo_cache(token_handler_a.utxo_cache, 1)


def test_token_req_handler_doStaticValidation_MINT_PUBLIC_success(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.mint(outputs)
    try:
        token_handler_a.doStaticValidation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the doStaticValidation method")


def test_token_req_handler_doStaticValidation_XFER_PUBLIC_success(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.transfer(inputs, outputs)
    try:
        token_handler_a.doStaticValidation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the doStaticValidation method")


def test_token_req_handler_doStaticValidation_GET_UTXO_success(
    helpers,
    addresses,
    token_handler_a
):
    address1 = addresses[0]
    request = helpers.request.get_utxo(address1)
    try:
        token_handler_a.doStaticValidation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the doStaticValidation method")


def test_token_req_handler_doStaticValidation_invalid_txn_type(
    helpers,
    addresses,
    token_handler_a
):
    address1 = addresses[0]
    request = helpers.request.get_utxo(address1)
    request.operation[TXN_TYPE] = 'Invalid TXN_TYPE'
    with pytest.raises(InvalidClientRequest):
        token_handler_a.doStaticValidation(request)


# TODO: This should validate that the sum of the outputs is equal to the sum of the inputs
def test_token_req_handler_validate_XFER_PUBLIC_success(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.transfer(inputs, outputs)
    try:
        token_handler_a.validate(request)
    except Exception:
        pytest.fail("This test failed to validate")


def test_token_req_handler_validate_XFER_PUBLIC_invalid(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 2)}]
    outputs = [{"address": address1, "amount": 40}]
    request = helpers.request.transfer(inputs, outputs)
    # This test should raise an issue because the inputs are not on the ledger
    with pytest.raises(InvalidClientMessageException):
        token_handler_a.validate(request)


def test_token_req_handler_validate_XFER_PUBLIC_invalid_overspend(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 40}]
    request = helpers.request.transfer(inputs, outputs)
    # This test is expected to fail because
    with pytest.raises(InsufficientFundsError):
        token_handler_a.validate(request)


def test_token_req_handler_validate_XFER_PUBLIC_invalid_underspend(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 1}, {"address": address2, "amount": 1}]
    request = helpers.request.transfer(inputs, outputs)
    # This test is expected to fail because
    with pytest.raises(ExtraFundsError):
        token_handler_a.validate(request)


def test_token_req_handler_apply_xfer_public_success(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 30}, {"address": address2, "amount": 30}]
    request = helpers.request.transfer(inputs, outputs)
    # test xfer now
    address1 = address1.replace("pay:sov:", "")
    address2 = address2.replace("pay:sov:", "")
    pre_apply_outputs_addr_1 = token_handler_a.utxo_cache.get_unspent_outputs(address1)
    pre_apply_outputs_addr_2 = token_handler_a.utxo_cache.get_unspent_outputs(address2)
    assert pre_apply_outputs_addr_1 == [Output(address1, 1, 40)]
    assert pre_apply_outputs_addr_2 == [Output(address2, 1, 60)]
    token_handler_a.apply(request, CONS_TIME)
    post_apply_outputs_addr_1 = token_handler_a.utxo_cache.get_unspent_outputs(address1)
    post_apply_outputs_addr_2 = token_handler_a.utxo_cache.get_unspent_outputs(address2)
    assert post_apply_outputs_addr_1 == [Output(address1, 1, 40), Output(address1, 2, 30)]
    assert post_apply_outputs_addr_2 == [Output(address2, 2, 30)]


def test_token_req_handler_apply_xfer_public_invalid(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 3)}]
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.transfer(inputs, outputs)

    # test xfer now
    # This raises a OperationError because the input transaction isn't already in the UTXO_Cache
    with pytest.raises(OperationError):
        token_handler_a.apply(request, CONS_TIME)


def test_token_req_handler_apply_MINT_PUBLIC_success(
    helpers,
    addresses,
    token_handler_a
):
    address = helpers.wallet.create_address()
    outputs = [{"address": address, "amount": 100}]
    request = helpers.request.mint(outputs)
    pre_apply_outputs = token_handler_a.utxo_cache.get_unspent_outputs(address.replace("pay:sov:", ""))
    assert pre_apply_outputs == []
    # Applies the MINT_PUBLIC transaction request to the UTXO cache
    token_handler_a.apply(request, CONS_TIME)
    post_apply_outputs = token_handler_a.utxo_cache.get_unspent_outputs(address.replace("pay:sov:", ""))
    assert post_apply_outputs[0].amount == 100


# We expect this test should pass, but in the future, we may want to exclude this case where MINT_PUBLIC txn has INPUTS
def test_token_req_handler_apply_MINT_PUBLIC_success_with_inputs(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.mint(outputs)
    request.operation[INPUTS] = [[address1, 1]]

    seq_no, txn = token_handler_a.apply(request, CONS_TIME)


def test_token_req_handler_apply_MINT_PUBLIC_success_with_inputs(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.mint(outputs)
    request.operation[INPUTS] = [[address1, 1]]

    seq_no, txn = token_handler_a.apply(request, CONS_TIME)

    expected = TxnResponse(
        MINT_PUBLIC,
        request.operation,
        signatures=request.signatures,
        req_id=request.reqId,
        frm=request._identifier,
    ).form_response()

    assert get_payload_data(txn) == get_payload_data(expected)
    assert get_req_id(txn) == get_req_id(expected)
    assert get_from(txn) == get_from(expected)
    assert get_sorted_signatures(txn) == get_sorted_signatures(txn)


def test_token_req_handler_updateState_XFER_PUBLIC_success(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    seq_no = 1

    inputs = [{"source": utxo_from_addr_and_seq_no(address1, seq_no)}]
    outputs = [{"address": address2, "amount": 40}]
    request = helpers.request.transfer(inputs, outputs)
    txn = reqToTxn(request)
    append_txn_metadata(txn, seq_no=seq_no)

    token_handler_a.validate(request)
    token_handler_a.updateState([txn])

    state_key = TokenReqHandler.create_state_key(address1.replace("pay:sov:", ""), seq_no)
    key = token_handler_a.utxo_cache._create_key(Output(address1.replace("pay:sov:", ""), seq_no, 60))
    assert token_handler_a.utxo_cache._store._has_key(key)
    try:
        token_handler_a.state.get(state_key, False)
    except Exception:
        pytest.fail("This state key isn't in the state")


def test_token_req_handler_onBatchCreated_success(
    addresses,
    token_handler_a,
    nodeSet
):
    address = addresses[0]
    output = Output(address, 10, 100)
    # add output to UTXO Cache
    token_handler_a.utxo_cache.add_output(output)
    state_root = nodeSet[1].master_replica.stateRootHash(TOKEN_LEDGER_ID)
    # run onBatchCreated
    token_handler_a.onBatchCreated(state_root, CONS_TIME)
    # Verify onBatchCreated worked properly
    key = token_handler_a.utxo_cache._create_key(output)
    assert token_handler_a.utxo_cache.un_committed[0][0] == state_root
    assert key in token_handler_a.utxo_cache.un_committed[0][1]
    assert '{}:{}'.format(str(output.seqNo), str(output.amount)) in token_handler_a.utxo_cache.un_committed[0][1][key]


def test_token_req_handler_onBatchRejected_success(addresses, token_handler_a):
    address1 = addresses[0]
    token_handler_a._add_new_output(Output(address1, 40, 100))
    token_handler_a.onBatchRejected()
    assert token_handler_a.utxo_cache.un_committed == []


# TODO: Is there a way to only use a single token handler?
def test_token_req_handler_commit_success(
    helpers,
    addresses,
    token_handler_b,
    nodeSet
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address1, 1)}]
    outputs = [{"address": address1, "amount": 30}, {"address": address2, "amount": 30}]
    request = helpers.request.transfer(inputs, outputs)

    # apply transaction
    state_root = nodeSet[1].master_replica.stateRootHash(TOKEN_LEDGER_ID)
    txn_root = nodeSet[1].master_replica.txnRootHash(TOKEN_LEDGER_ID)
    token_handler_b.apply(request, CONS_TIME)
    address1 = address1.replace("pay:sov:", "")
    address2 = address2.replace("pay:sov:", "")
    new_state_root = nodeSet[1].master_replica.stateRootHash(TOKEN_LEDGER_ID)
    new_txn_root = nodeSet[1].master_replica.txnRootHash(TOKEN_LEDGER_ID)
    # add batch
    token_handler_b.onBatchCreated(base58.b58decode(new_state_root.encode()), CONS_TIME)
    # commit batch
    assert token_handler_b.utxo_cache.get_unspent_outputs(address1, True) == [Output(address1, 1, 40)]
    assert token_handler_b.utxo_cache.get_unspent_outputs(address2, True) == [Output(address2, 1, 60)]
    commit_ret_val = token_handler_b.commit(1, new_state_root, new_txn_root, None)
    assert token_handler_b.utxo_cache.get_unspent_outputs(address1, True) == [Output(address1, 2, 30)]
    assert token_handler_b.utxo_cache.get_unspent_outputs(address2, True) == [
        Output(address2, 1, 60),
        Output(address2, 2, 30)
    ]
    assert new_state_root != state_root
    assert new_txn_root != txn_root


def test_token_req_handler_get_query_response_success(
    helpers,
    addresses,
    token_handler_a
):
    address1 = addresses[0]
    request = helpers.request.get_utxo(address1)
    results = token_handler_a.get_query_response(request)

    state_proof = results.pop(STATE_PROOF)
    address1 = address1.replace("pay:sov:", "")
    assert state_proof
    assert results == {
        ADDRESS: address1,
        TXN_TYPE: GET_UTXO,
        OUTPUTS: [Output(address=address1, seq_no=1, value=40)],
        IDENTIFIER: base58.b58encode(base58.b58decode_check(address1)).decode(),
        TXN_PAYLOAD_METADATA_REQ_ID: request.reqId
    }


def test_token_req_handler_get_query_response_invalid_txn_type(
    helpers,
    addresses,
    token_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address1, 1)}]
    outputs = [{"address": address2, "amount": 40}]
    request = helpers.request.transfer(inputs, outputs)
    # A KeyError is expected because get_query_responses can only handle query transaction types
    with pytest.raises(KeyError):
        token_handler_a.get_query_response(request)


def test_token_req_handler_get_all_utxo_success(
    helpers,
    addresses,
    token_handler_a
):
    [address1, _] = addresses
    request = helpers.request.get_utxo(address1)
    results = token_handler_a.get_query_response(request)

    state_proof = results.pop(STATE_PROOF)

    assert state_proof
    assert results == {
        ADDRESS: address1.replace("pay:sov:", ""),
        TXN_TYPE: GET_UTXO,
        OUTPUTS: [
            Output(address=address1.replace("pay:sov:", ""), seq_no=1, value=40)
        ],
        IDENTIFIER: base58.b58encode(base58.b58decode_check(address1.replace("pay:sov:", ""))).decode(),
        TXN_PAYLOAD_METADATA_REQ_ID: request.reqId
    }


def test_token_req_handler_create_state_key_success(addresses, token_handler_a):
    address1 = addresses[0]
    state_key = token_handler_a.create_state_key(address1, 40)
    assert state_key.decode() == '{}:40'.format(address1)


# This test acts as a test for the static method of sum_inputs too
def test_token_req_handler_sum_inputs_success(helpers, token_handler_a):
    address = helpers.inner.wallet.create_address()

    # Verify no outputs
    pre_add_outputs = token_handler_a.utxo_cache.get_unspent_outputs(address)
    assert pre_add_outputs == []

    # add and verify new unspent output added
    token_handler_a.utxo_cache.add_output(Output(address, 5, 150))
    post_add_outputs = token_handler_a.utxo_cache.get_unspent_outputs(address)
    assert post_add_outputs == [Output(address, 5, 150)]

    # add second unspent output and verify
    token_handler_a.utxo_cache.add_output(Output(address, 6, 100))
    post_second_add_outputs = token_handler_a.utxo_cache.get_unspent_outputs(address)
    assert post_second_add_outputs == [Output(address, 5, 150), Output(address, 6, 100)]

    # Verify sum_inputs is working properly
    inputs = [{"address": address, "seqNo": 5}, {"address": address, "seqNo": 6}]
    outputs = []
    request = helpers.inner.request.transfer(inputs, outputs)
    sum_inputs = token_handler_a._sum_inputs(request)
    assert sum_inputs == 250


# This test acts as a test for the static method of spent_inputs too
def test_token_req_handler_spend_input_success(helpers, token_handler_a):
    address = helpers.wallet.create_address()
    # add input to address
    token_handler_a.utxo_cache.add_output(Output(address, 7, 200))

    # spend input to address
    token_handler_a._spend_input(address, 7)
    unspent_outputs = token_handler_a.utxo_cache.get_unspent_outputs(address)
    assert unspent_outputs == []


# This test acts as a test for the static method of add_new_output too
def test_token_req_handler_add_new_output_success(helpers, token_handler_a):
    address = helpers.wallet.create_address()
    token_handler_a._add_new_output(Output(address, 8, 350))
    unspent_outputs = token_handler_a.utxo_cache.get_unspent_outputs(address)
    assert unspent_outputs == [Output(address, 8, 350)]


class TestValidateMintPublic():
    @pytest.fixture(autouse=True)
    def init(self, helpers):
        self.addresses = helpers.wallet.create_new_addresses(2)
        self.handler = helpers.node.get_token_req_handler()

    @pytest.fixture()
    def mint_request(self, helpers):
        outputs = [{"address": address, "amount": 1000} for address in self.addresses]
        request = helpers.request.mint(outputs)
        return request

    def sign_with_quorum(self, helpers, request, wallets):
        quorum = wallets[:math.ceil(len(wallets) / 2)]
        request.signatures = {}
        request = helpers.wallet.sign_request(request, quorum)
        return request

    def test_less_than_min_trustees(self, helpers, mint_request):
        mint_request.signatures.popitem()
        with pytest.raises(InvalidClientMessageException):
            self.handler.validate(mint_request)

    def test_steward_with_trustees(
        self,
        helpers,
        mint_request,
        steward_wallets
    ):
        mint_request.signatures.popitem()
        mint_request = helpers.wallet.sign_request(
            mint_request,
            steward_wallets[0:1]
        )
        with pytest.raises(UnauthorizedClientRequest):
            self.handler.validate(mint_request)

    def test_valid_request(self, helpers, mint_request):
        assert self.handler.validate(mint_request)

    @pytest.mark.skip
    def test_quorum_trustees(self, helpers, mint_request, trustee_wallets):
        mint_request = self.sign_with_quorum(
            helpers,
            mint_request,
            trustee_wallets
        )
        assert self.handler.validate(mint_request)

    @pytest.mark.skip
    def test_no_quorum_trustees(self, helpers, mint_request, trustee_wallets):
        mint_request = self.sign_with_quorum(
            helpers,
            mint_request,
            trustee_wallets
        )
        mint_request.signatures.popitem()
        with pytest.raises(InvalidClientMessageException):
            self.handler.validate(mint_request)

    @pytest.mark.skip
    def test_quorum_increased_trustees(
        self,
        helpers,
        mint_request,
        increased_trustees
    ):
        mint_request = self.sign_with_quorum(
            helpers,
            mint_request,
            increased_trustees
        )
        assert self.handler.validate(mint_request)

    @pytest.mark.skip
    def test_no_quorum_increased_trustees(
        self,
        helpers,
        mint_request,
        increased_trustees
    ):
        mint_request = self.sign_with_quorum(
            helpers,
            mint_request,
            increased_trustees
        )
        mint_request.signatures.popitem()
        with pytest.raises(InvalidClientMessageException):
            self.handler.validate(mint_request)
