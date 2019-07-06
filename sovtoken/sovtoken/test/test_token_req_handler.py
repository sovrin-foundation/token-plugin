import math
from collections import OrderedDict

import base58
import pytest
from sovtoken.request_handlers.token_utils import commit_to_utxo_cache
from sovtoken.test.helper import libsovtoken_address_to_address
from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no

from plenum.common.constants import (IDENTIFIER, STATE_PROOF,
                                     TXN_PAYLOAD_METADATA_REQ_ID, TXN_TYPE)
from plenum.common.exceptions import (InvalidClientMessageException,
                                      InvalidClientRequest, OperationError,
                                      UnauthorizedClientRequest)
from plenum.common.txn_util import (append_txn_metadata, get_from,
                                    get_payload_data, get_req_id, reqToTxn)
from sovtoken.constants import (ADDRESS, GET_UTXO, INPUTS, MINT_PUBLIC,
                                OUTPUTS, TOKEN_LEDGER_ID, UTXO_CACHE_LABEL, XFER_PUBLIC)
from sovtoken.exceptions import ExtraFundsError, InsufficientFundsError, TokenValueError
from sovtoken.test.txn_response import TxnResponse, get_sorted_signatures
from sovtoken.token_req_handler import TokenReqHandler
from sovtoken.types import Output

# Test Constants
VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"
CONS_TIME = 1518541344


@pytest.fixture
def xfer_handler_a(helpers):
    h = helpers.node.xfer_handler
    old_head = h.state.committedHead
    yield h
    h.state.revertToHead(old_head)
    # TODO: this is a function fixture. Do we need this revert there?
    # h.onBatchRejected()


@pytest.fixture
def get_utxo_handler(helpers):
    return helpers.node.get_utxo_handler


@pytest.fixture
def mint_handler(helpers):
    return helpers.node.mint_handler


@pytest.fixture
def xfer_handler_b(nodeSet):
    h = nodeSet[1].write_manager.request_handlers[XFER_PUBLIC][0]
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
    outputs = [{"address": "pay:sov:" + addresses[0], "amount": 40},
               {"address": "pay:sov:" + addresses[1], "amount": 60}]
    helpers.general.do_mint(outputs)
    return addresses


def test_token_req_handler_commit_batch_different_state_root(
        xfer_handler_a
):
    utxo_cache = xfer_handler_a.database_manager.get_store(UTXO_CACHE_LABEL)
    with pytest.raises(TokenValueError):
        commit_to_utxo_cache(utxo_cache, 1)


def test_token_req_handler_static_validation_MINT_PUBLIC_success(
        helpers,
        addresses,
        xfer_handler_a
):
    [address1, address2] = addresses
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.mint(outputs)
    try:
        xfer_handler_a.static_validation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the static_validation method")


def test_token_req_handler_static_validation_XFER_PUBLIC_success(
        helpers,
        addresses,
        xfer_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.transfer(inputs, outputs)
    try:
        xfer_handler_a.static_validation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the static_validation method")


def test_token_req_handler_static_validation_GET_UTXO_success(
        helpers,
        addresses,
        xfer_handler_a
):
    address1 = addresses[0]
    request = helpers.request.get_utxo(address1)
    try:
        xfer_handler_a.static_validation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the static_validation method")


# TODO: This should validate that the sum of the outputs is equal to the sum of the inputs
# def test_token_req_handler_validate_XFER_PUBLIC_success(
#         helpers,
#         addresses,
#         xfer_handler_a
# ):
#     [address1, address2] = addresses
#     inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
#     outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
#     request = helpers.request.transfer(inputs, outputs)
#     try:
#         xfer_handler_a.dynamic_validation(request)
#     except Exception:
        pytest.fail("This test failed to validate")


def test_token_req_handler_validate_XFER_PUBLIC_invalid(
        helpers,
        addresses,
        xfer_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 2)}]
    outputs = [{"address": address1, "amount": 40}]
    request = helpers.request.transfer(inputs, outputs)
    # This test should raise an issue because the inputs are not on the ledger
    with pytest.raises(InvalidClientMessageException):
        xfer_handler_a.dynamic_validation(request)


def test_token_req_handler_validate_XFER_PUBLIC_invalid_overspend(
        helpers,
        addresses,
        xfer_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 40}]
    request = helpers.request.transfer(inputs, outputs)
    # This test is expected to fail because
    with pytest.raises(InsufficientFundsError):
        xfer_handler_a.dynamic_validation(request)


def test_token_req_handler_validate_XFER_PUBLIC_invalid_underspend(
        helpers,
        addresses,
        xfer_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 1}, {"address": address2, "amount": 1}]
    request = helpers.request.transfer(inputs, outputs)
    # This test is expected to fail because
    with pytest.raises(ExtraFundsError):
        xfer_handler_a.dynamic_validation(request)


def test_token_req_handler_apply_xfer_public_success(
        helpers,
        addresses,
        xfer_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 1)}]
    outputs = [{"address": address1, "amount": 30}, {"address": address2, "amount": 30}]
    request = helpers.request.transfer(inputs, outputs)
    # test xfer now
    address1 = libsovtoken_address_to_address(address1)
    address2 = libsovtoken_address_to_address(address2)
    utxo_cache = xfer_handler_a.database_manager.get_store(UTXO_CACHE_LABEL)
    pre_apply_outputs_addr_1 = utxo_cache.get_unspent_outputs(address1)
    pre_apply_outputs_addr_2 = utxo_cache.get_unspent_outputs(address2)
    assert pre_apply_outputs_addr_1 == [Output(address1, 1, 40)]
    assert pre_apply_outputs_addr_2 == [Output(address2, 1, 60)]
    xfer_handler_a.apply_request(request, CONS_TIME, None)
    post_apply_outputs_addr_1 = utxo_cache.get_unspent_outputs(address1)
    post_apply_outputs_addr_2 = utxo_cache.get_unspent_outputs(address2)
    assert post_apply_outputs_addr_1 == [Output(address1, 1, 40), Output(address1, 2, 30)]
    assert post_apply_outputs_addr_2 == [Output(address2, 2, 30)]


def test_token_req_handler_apply_xfer_public_invalid(
        helpers,
        addresses,
        xfer_handler_a
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address2, 3)}]
    outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
    request = helpers.request.transfer(inputs, outputs)

    # test xfer now
    # This raises a OperationError because the input transaction isn't already in the UTXO_Cache
    with pytest.raises(OperationError):
        xfer_handler_a.apply_request(request, CONS_TIME, None)


def test_token_req_handler_apply_MINT_PUBLIC_success(
        helpers,
        addresses,
        mint_handler
):
    address = helpers.wallet.create_address()
    outputs = [{"address": address, "amount": 100}]
    request = helpers.request.mint(outputs)
    utxo_cache = mint_handler.database_manager.get_store(UTXO_CACHE_LABEL)
    pre_apply_outputs = utxo_cache.get_unspent_outputs(libsovtoken_address_to_address(address))
    assert pre_apply_outputs == []
    # Applies the MINT_PUBLIC transaction request to the UTXO cache
    mint_handler.apply_request(request, CONS_TIME, None)
    post_apply_outputs = utxo_cache.get_unspent_outputs(libsovtoken_address_to_address(address))
    assert post_apply_outputs[0].amount == 100


# We expect this test should pass, but in the future, we may want to exclude this case where MINT_PUBLIC txn has INPUTS
# def test_token_req_handler_apply_MINT_PUBLIC_success_with_inputs(
#         helpers,
#         addresses,
#         xfer_handler_a
# ):
#     [address1, address2] = addresses
#     outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
#     request = helpers.request.mint(outputs)
#     request.operation[INPUTS] = [[address1, 1]]
#
#     seq_no, txn = xfer_handler_a.apply_request(request, CONS_TIME, None)


# def test_token_req_handler_apply_MINT_PUBLIC_success_with_inputs(
#         helpers,
#         addresses,
#         mint_handler
# ):
#     [address1, address2] = addresses
#     outputs = [{"address": address1, "amount": 40}, {"address": address2, "amount": 20}]
#     request = helpers.request.mint(outputs)
#     request.operation[INPUTS] = [[address1, 1]]
#
#     seq_no, txn = mint_handler.apply_request(request, CONS_TIME, None)
#
#     expected = TxnResponse(
#         MINT_PUBLIC,
#         request.operation,
#         signatures=request.signatures,
#         req_id=request.reqId,
#         frm=request._identifier,
#     ).form_response()
#
#     assert get_payload_data(txn) == get_payload_data(expected)
#     assert get_req_id(txn) == get_req_id(expected)
#     assert get_from(txn) == get_from(expected)
#     assert get_sorted_signatures(txn) == get_sorted_signatures(txn)


def test_token_req_handler_update_state_XFER_PUBLIC_success(
        helpers,
        addresses,
        xfer_handler_a
):
    [address1, address2] = addresses
    seq_no = 1

    inputs = [{"source": utxo_from_addr_and_seq_no(address1, seq_no)}]
    outputs = [{"address": address2, "amount": 40}]
    request = helpers.request.transfer(inputs, outputs)
    txn = reqToTxn(request)
    append_txn_metadata(txn, seq_no=seq_no)

    xfer_handler_a.dynamic_validation(request)
    xfer_handler_a.update_state(txn, None, request)

    state_key = TokenReqHandler.create_state_key(libsovtoken_address_to_address(address1), seq_no)
    utxo_cache = xfer_handler_a.database_manager.get_store(UTXO_CACHE_LABEL)
    key = utxo_cache._create_key(Output(libsovtoken_address_to_address(address1), seq_no, 60))
    assert utxo_cache._store._has_key(key)
    try:
        xfer_handler_a.state.get(state_key, False)
    except Exception:
        pytest.fail("This state key isn't in the state")


# def test_token_req_handler_onBatchCreated_success(
#         addresses,
#         xfer_handler_a,
#         nodeSet
# ):
#     address = addresses[0]
#     output = Output(address, 10, 100)
#     # add output to UTXO Cache
#     utxo_cache = xfer_handler_a.database_manager.get_store(UTXO_CACHE_LABEL)
#     utxo_cache.add_output(output)
#     state_root = nodeSet[1].master_replica.stateRootHash(TOKEN_LEDGER_ID)
#     # run onBatchCreated
#     xfer_handler_a.onBatchCreated(state_root, CONS_TIME)
#     # Verify onBatchCreated worked properly
#     key = utxo_cache._create_key(output)
#     assert utxo_cache.un_committed[0][0] == state_root
#     assert key in utxo_cache.un_committed[0][1]
#     assert '{}:{}'.format(str(output.seqNo), str(output.amount)) in utxo_cache.un_committed[0][1][key]
#
#
# def test_token_req_handler_onBatchRejected_success(addresses, xfer_handler_a):
#     address1 = addresses[0]
#     xfer_handler_a._add_new_output(Output(address1, 40, 100))
#     xfer_handler_a.onBatchRejected()
#     utxo_cache = xfer_handler_a.database_manager.get_store(UTXO_CACHE_LABEL)
#     assert utxo_cache.un_committed == []
#
#
# # TODO: Is there a way to only use a single token handler?
# def test_token_req_handler_commit_success(
#         helpers,
#         addresses,
#         xfer_handler_b,
#         nodeSet
# ):
#     [address1, address2] = addresses
#     inputs = [{"source": utxo_from_addr_and_seq_no(address1, 1)}]
#     outputs = [{"address": address1, "amount": 30}, {"address": address2, "amount": 30}]
#     request = helpers.request.transfer(inputs, outputs)
#
#     # apply transaction
#     state_root = nodeSet[1].master_replica.stateRootHash(TOKEN_LEDGER_ID)
#     txn_root = nodeSet[1].master_replica.txnRootHash(TOKEN_LEDGER_ID)
#     xfer_handler_b.apply_request(request, CONS_TIME, None)
#     address1 = address1.replace("pay:sov:", "")
#     address2 = address2.replace("pay:sov:", "")
#     new_state_root = nodeSet[1].master_replica.stateRootHash(TOKEN_LEDGER_ID)
#     new_txn_root = nodeSet[1].master_replica.txnRootHash(TOKEN_LEDGER_ID)
#     # add batch
#     xfer_handler_b.onBatchCreated(base58.b58decode(new_state_root.encode()), CONS_TIME)
#     # commit batch
#     utxo_cache = xfer_handler_b.database_manager.get_store(UTXO_CACHE_LABEL)
#     assert utxo_cache.get_unspent_outputs(address1, True) == [Output(address1, 1, 40)]
#     assert utxo_cache.get_unspent_outputs(address2, True) == [Output(address2, 1, 60)]
#     commit_ret_val = xfer_handler_b.commit(1, new_state_root, new_txn_root, None)
#     assert utxo_cache.get_unspent_outputs(address1, True) == [Output(address1, 2, 30)]
#     assert utxo_cache.get_unspent_outputs(address2, True) == [
#         Output(address2, 1, 60),
#         Output(address2, 2, 30)
#     ]
#     assert new_state_root != state_root
#     assert new_txn_root != txn_root


def test_token_req_handler_get_result_success(
        helpers,
        addresses,
        get_utxo_handler
):
    address1 = addresses[0]
    request = helpers.request.get_utxo(address1)
    results = get_utxo_handler.get_result(request)

    state_proof = results.pop(STATE_PROOF)
    address1 = libsovtoken_address_to_address(address1)
    assert state_proof
    assert results == {
        ADDRESS: address1,
        TXN_TYPE: GET_UTXO,
        OUTPUTS: [Output(address=address1, seq_no=1, value=40)],
        IDENTIFIER: base58.b58encode(base58.b58decode_check(address1)).decode(),
        TXN_PAYLOAD_METADATA_REQ_ID: request.reqId
    }


def test_token_req_handler_get_result_invalid_txn_type(
        helpers,
        addresses,
        get_utxo_handler
):
    [address1, address2] = addresses
    inputs = [{"source": utxo_from_addr_and_seq_no(address1, 1)}]
    outputs = [{"address": address2, "amount": 40}]
    request = helpers.request.transfer(inputs, outputs)
    # A KeyError is expected because get_results can only handle query transaction types
    with pytest.raises(KeyError):
        get_utxo_handler.get_result(request)


def test_token_req_handler_get_all_utxo_success(
        helpers,
        addresses,
        get_utxo_handler
):
    [address1, _] = addresses
    request = helpers.request.get_utxo(address1)
    results = get_utxo_handler.get_result(request)

    state_proof = results.pop(STATE_PROOF)

    assert state_proof
    assert results == {
        ADDRESS: libsovtoken_address_to_address(address1),
        TXN_TYPE: GET_UTXO,
        OUTPUTS: [
            Output(address=libsovtoken_address_to_address(address1), seq_no=1, value=40)
        ],
        IDENTIFIER: base58.b58encode(base58.b58decode_check(libsovtoken_address_to_address(address1))).decode(),
        TXN_PAYLOAD_METADATA_REQ_ID: request.reqId
    }


# def test_token_req_handler_create_state_key_success(addresses, xfer_handler_a):
#     address1 = addresses[0]
#     state_key = xfer_handler_a.create_state_key(address1, 40)
#     assert state_key.decode() == '{}:40'.format(address1)
#
#
# # This test acts as a test for the static method of sum_inputs too
# def test_token_req_handler_sum_inputs_success(helpers, xfer_handler_a):
#     address = helpers.inner.wallet.create_address()
#
#     # Verify no outputs
#     utxo_cache = xfer_handler_a.database_manager.get_store(UTXO_CACHE_LABEL)
#     pre_add_outputs = utxo_cache.get_unspent_outputs(address)
#     assert pre_add_outputs == []
#
#     # add and verify new unspent output added
#     utxo_cache.add_output(Output(address, 5, 150))
#     post_add_outputs = utxo_cache.get_unspent_outputs(address)
#     assert post_add_outputs == [Output(address, 5, 150)]
#
#     # add second unspent output and verify
#     utxo_cache.add_output(Output(address, 6, 100))
#     post_second_add_outputs = utxo_cache.get_unspent_outputs(address)
#     assert post_second_add_outputs == [Output(address, 5, 150), Output(address, 6, 100)]
#
#     # Verify sum_inputs is working properly
#     inputs = [{"address": address, "seqNo": 5}, {"address": address, "seqNo": 6}]
#     outputs = []
#     request = helpers.inner.request.transfer(inputs, outputs)
#     sum_inputs = xfer_handler_a._sum_inputs(request)
#     assert sum_inputs == 250
#
#
# # This test acts as a test for the static method of add_new_output too
# def test_token_req_handler_add_new_output_success(helpers, xfer_handler_a):
#     address = helpers.wallet.create_address()
#     xfer_handler_a._add_new_output(Output(address, 8, 350))
#     utxo_cache = xfer_handler_a.database_manager.get_store(UTXO_CACHE_LABEL)
#     unspent_outputs = utxo_cache.get_unspent_outputs(address)
#     assert unspent_outputs == [Output(address, 8, 350)]


class TestValidateMintPublic():
    @pytest.fixture(autouse=True)
    def init(self, helpers):
        self.addresses = helpers.wallet.create_new_addresses(2)
        self.handler = helpers.node.xfer_handler

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
            self.handler.dynamic_validation(mint_request)

    # def test_steward_with_trustees(
    #         self,
    #         helpers,
    #         mint_request,
    #         steward_wallets
    # ):
    #     mint_request.signatures.popitem()
    #     mint_request = helpers.wallet.sign_request(
    #         mint_request,
    #         steward_wallets[0:1]
    #     )
    #     with pytest.raises(UnauthorizedClientRequest):
    #         self.handler.dynamic_validation(mint_request)
    #
    # def test_valid_request(self, helpers, mint_request):
    #     assert self.handler.dynamic_validation(mint_request)

    @pytest.mark.skip
    def test_quorum_trustees(self, helpers, mint_request, trustee_wallets):
        mint_request = self.sign_with_quorum(
            helpers,
            mint_request,
            trustee_wallets
        )
        assert self.handler.dynamic_validation(mint_request)

    @pytest.mark.skip
    def test_no_quorum_trustees(self, helpers, mint_request, trustee_wallets):
        mint_request = self.sign_with_quorum(
            helpers,
            mint_request,
            trustee_wallets
        )
        mint_request.signatures.popitem()
        with pytest.raises(InvalidClientMessageException):
            self.handler.dynamic_validation(mint_request)

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
        assert self.handler.dynamic_validation(mint_request)

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
            self.handler.dynamic_validation(mint_request)
