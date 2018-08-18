from collections import OrderedDict

import base58
import math
import pytest
from plenum.common.signer_simple import SimpleSigner

from plenum.common.constants import TXN_TYPE, STATE_PROOF, TRUSTEE_STRING, \
    TARGET_NYM, VERKEY
from plenum.common.exceptions import InvalidClientRequest, UnauthorizedClientRequest, InvalidClientMessageException, \
    OperationError
from plenum.common.request import Request
from plenum.common.txn_util import reqToTxn, append_txn_metadata, get_payload_data, \
    get_req_id, get_from
from plenum.common.util import randomString
from sovtoken.token_req_handler import TokenReqHandler
from sovtoken.exceptions import InsufficientFundsError, ExtraFundsError, UTXOAlreadySpentError, UTXOError

# TEST CONSTANTS
from sovtoken.types import Output
from sovtoken.constants import XFER_PUBLIC, MINT_PUBLIC, SIGS, \
    OUTPUTS, INPUTS, GET_UTXO, ADDRESS, TOKEN_LEDGER_ID, RESULT

from sovtoken.test.txn_response import TxnResponse, get_sorted_signatures
from sovtoken.util import verkey_to_address

VALID_ADDR_1, VALID_ADDR_2 = (None, None)

(VALID_ADDR_3, VALID_ADDR_4, VALID_ADDR_5, VALID_ADDR_6, VALID_ADDR_7) = \
    (verkey_to_address(SimpleSigner().verkey) for _ in range(5))


VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"
VALID_REQID = 1517423828260117
CONS_TIME = 1518541344
PROTOCOL_VERSION = 1
SIGNATURES = {'B8fV7naUqLATYocqu7yZ8W':
                  '27BVCWvThxMV9pzqz3JepMLVKww7MmreweYjh15LkwvAH4qwYAMbZWeYr6E6LcQexYAikTHo212U1NKtG8Gr2PPP',
              'CA4bVFDU4GLbX8xZju811o':
                  '3A1Pmkox4SzYRavTj9toJtGBr1Jy9JvTTnHz5gkS5dGnY3PhDcsKpQCBfLhYbKqFvpZKaLPGT48LZKzUVY4u78Ki',
              'E7QRhdcnhAwA6E46k9EtZo':
                  'MsZsG2uQHFqMvAsQsx5dnQiqBjvxYS1QsVjqHkbvdS2jPdZQhJfackLQbxQ4RDNUrDBy8Na6yZcKbjK2feun7fg',
              'M9BJDuS24bqbJNvBRsoGg3':
                  '5BzS7J7uSuUePRzLdF5BL5LPvnXxzQyB5BqMT19Hz8QjEyb41Mum71TeNvPW9pKbhnDK12Pciqw9WRHUvsfwdYT5'}


@pytest.fixture
def setup(SF_address, seller_address):
    global VALID_ADDR_1, VALID_ADDR_2
    VALID_ADDR_1, VALID_ADDR_2 = seller_address, SF_address


@pytest.fixture
def node(setup, txnPoolNodeSet):
    a, b, c, d = txnPoolNodeSet
    nodes = [a, b, c, d]
    return nodes


@pytest.fixture
def token_handler_a(node):
    return node[0].ledger_to_req_handler[TOKEN_LEDGER_ID]


@pytest.fixture
def token_handler_b(node):
    return node[1].ledger_to_req_handler[TOKEN_LEDGER_ID]


@pytest.fixture
def token_handler_c(node):
    return node[2].ledger_to_req_handler[TOKEN_LEDGER_ID]


@pytest.fixture
def token_handler_d(node):
    return node[3].ledger_to_req_handler[TOKEN_LEDGER_ID]


def test_token_req_handler_doStaticValidation_MINT_PUBLIC_success(token_handler_a):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: MINT_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 40
                                                      }]},
                      None, SIGNATURES, 1)
    try:
        token_handler_a.doStaticValidation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the doStaticValidation method")


def test_token_req_handler_doStaticValidation_XFER_PUBLIC_success(token_handler_a):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 20
                                                      }],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "seqNo": 1
                                                      }],
                                                      SIGS: ['']}, None, SIGNATURES, 1)
    try:
        token_handler_a.doStaticValidation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the doStaticValidation method")


def test_token_req_handler_doStaticValidation_GET_UTXO_success(token_handler_a):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: GET_UTXO, ADDRESS: VALID_ADDR_1},
                      None, SIGNATURES, 1)
    try:
        token_handler_a.doStaticValidation(request)
    except InvalidClientRequest:
        pytest.fail("This test failed because error is not None")
    except Exception:
        pytest.fail("This test failed outside the doStaticValidation method")


def test_token_req_handler_doStaticValidation_invalid_txn_type(token_handler_a):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: 'INVALID TXN_TYPE', ADDRESS: VALID_ADDR_1},
                      None, SIGNATURES, 1)
    with pytest.raises(InvalidClientRequest):
        token_handler_a.doStaticValidation(request)


# TODO: This should validate that the sum of the outputs is equal to the sum of the inputs
def test_token_req_handler_validate_XFER_PUBLIC_success(public_minting, token_handler_a):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 20
                                                      }],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "seqNo": 1
                                                      }],
                                                      SIGS: []}, None, SIGNATURES, 1)
    try:
        token_handler_a.validate(request)
    except Exception:
        pytest.fail("This test failed to validate")


def test_token_req_handler_validate_XFER_PUBLIC_invalid(token_handler_a):
    operation = {
        TXN_TYPE: XFER_PUBLIC,
        OUTPUTS: [{
            "address": VALID_ADDR_2,
            "amount": 40
        }],
        INPUTS: [{
            "address": VALID_ADDR_3,
            "seqNo": 1
        }]
    }

    request = Request(
        VALID_IDENTIFIER,
        VALID_REQID,
        operation,
        None,
        SIGNATURES,
        1
    )
    # This test should raise an issue because the inputs are not on the ledger
    with pytest.raises(InvalidClientMessageException):
        token_handler_a.validate(request)


def test_token_req_handler_validate_XFER_PUBLIC_invalid_overspend(public_minting, token_handler_a):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 40
                                                      }],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "seqNo": 1}
                                                      ]}, None, SIGNATURES, 1)
    # This test is expected to fail because
    with pytest.raises(InsufficientFundsError):
        token_handler_a.validate(request)


def test_token_req_handler_validate_XFER_PUBLIC_invalid_underspend(public_minting, token_handler_a):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 1
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 1
                                                      }],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "seqNo": 1
                                                      }]}, None, SIGNATURES, 1)
    # This test is expected to fail because
    with pytest.raises(ExtraFundsError):
        token_handler_a.validate(request)


def test_token_req_handler_validate_MINT_PUBLIC_success(token_handler_a):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: MINT_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 40
                                                      }]},
                      None, SIGNATURES, 1)
    try:
        token_handler_a.validate(request)
    except Exception:
        pytest.fail("Validate seems to be working improperly")


def test_token_req_handler_validate_MINT_PUBLIC_invalid(token_handler_a):
    invalid_num_sigs = {'B8fV7naUqLATYocqu7yZ8W':
                            '27BVCWvThxMV9pzqz3JepMLVKww7MmreweYjh15LkwvAH4qwYAMbZWeYr6E6LcQexYAikTHo212U1NKtG8Gr2PPP',
                        'M9BJDuS24bqbJNvBRsoGg3':
                            '5BzS7J7uSuUePRzLdF5BL5LPvnXxzQyB5BqMT19Hz8QjEyb41Mum71TeNvPW9pKbhnDK12Pciqw9WRHUvsfwdYT5',
                        'E7QRhdcnhAwA6E46k9EtZo':
                            'MsZsG2uQHFqMvAsQsx5dnQiqBjvxYS1QsVjqHkbvdS2jPdZQhJfackLQbxQ4RDNUrDBy8Na6yZcKbjK2feun7fg'}
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: MINT_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 40
                                                      }], },
                      None, invalid_num_sigs, 1)
    with pytest.raises(UnauthorizedClientRequest):
        token_handler_a.validate(request)


def test_token_req_handler_apply_xfer_public_success(public_minting, token_handler_b):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 30}, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 30
                                                      }],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "seqNo": 1
                                                      }],
                                                      SIGS: ['']}, None, SIGNATURES, 1)
    # test xfer now
    pre_apply_outputs_addr_1 = token_handler_b.utxo_cache.get_unspent_outputs(VALID_ADDR_1)
    pre_apply_outputs_addr_2 = token_handler_b.utxo_cache.get_unspent_outputs(VALID_ADDR_2)
    assert pre_apply_outputs_addr_1 == [Output(VALID_ADDR_1, 1, 40)]
    assert pre_apply_outputs_addr_2 == [Output(VALID_ADDR_2, 1, 60)]
    token_handler_b.apply(request, CONS_TIME)
    post_apply_outputs_addr_1 = token_handler_b.utxo_cache.get_unspent_outputs(VALID_ADDR_1)
    post_apply_outputs_addr_2 = token_handler_b.utxo_cache.get_unspent_outputs(VALID_ADDR_2)
    assert post_apply_outputs_addr_1 == [Output(VALID_ADDR_1, 1, 40), Output(VALID_ADDR_1, 2, 30)]
    assert post_apply_outputs_addr_2 == [Output(VALID_ADDR_2, 2, 30)]
    token_handler_b.onBatchRejected()


def test_token_req_handler_apply_xfer_public_invalid(token_handler_b):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 40
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 20
                                                      }],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "seqNo": 3
                                                      }],
                                                      SIGS: ['']}, None, SIGNATURES, 1)
    # test xfer now
    # This raises a OperationError because the input transaction isn't already in the UTXO_Cache
    with pytest.raises(OperationError):
        token_handler_b.apply(request, CONS_TIME)
    token_handler_b.onBatchRejected()


def test_token_req_handler_apply_MINT_PUBLIC_success(token_handler_b):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: MINT_PUBLIC,
                                                      OUTPUTS: [{"address":VALID_ADDR_3, "amount": 100}]},
                      None, SIGNATURES, 1)
    pre_apply_outputs_addr_3 = token_handler_b.utxo_cache.get_unspent_outputs(VALID_ADDR_3)
    assert pre_apply_outputs_addr_3 == []
    # Applies the MINT_PUBLIC transaction request to the UTXO cache
    token_handler_b.apply(request, CONS_TIME)
    post_apply_outputs_addr_3 = token_handler_b.utxo_cache.get_unspent_outputs(VALID_ADDR_3)
    assert post_apply_outputs_addr_3[0].value == 100
    token_handler_b.onBatchRejected()


# We expect this test should pass, but in the future, we may want to exclude this case where MINT_PUBLIC txn has INPUTS
def test_token_req_handler_apply_MINT_PUBLIC_success_with_inputs(token_handler_b):
    data = {
        TXN_TYPE: MINT_PUBLIC,
        OUTPUTS: [{
            "address": VALID_ADDR_1,
            "amount": 40
        }, {
            "address": VALID_ADDR_2,
            "amount": 20
        }],
        INPUTS: [{"address": VALID_ADDR_1, "seqNo": 1}]
    }
    request = Request(VALID_IDENTIFIER, VALID_REQID, data, None, SIGNATURES, 1)
    seq_no, txn = token_handler_b.apply(request, CONS_TIME)

    expected = TxnResponse(
        MINT_PUBLIC,
        data,
        signatures=SIGNATURES,
        req_id=VALID_REQID,
        frm=VALID_IDENTIFIER,
    ).form_response()

    assert get_payload_data(txn) == get_payload_data(expected)
    assert get_req_id(txn) == get_req_id(expected)
    assert get_from(txn) == get_from(expected)
    assert get_sorted_signatures(txn) == get_sorted_signatures(txn)

    token_handler_b.onBatchRejected()


def test_token_req_handler_updateState_XFER_PUBLIC_success(public_minting, token_handler_b):
    seq_no = 1
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "amount": 40}],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "seqNo": seq_no}],
                                                      SIGS: ['']}, None, SIGNATURES, 2)
    txn = reqToTxn(request)
    append_txn_metadata(txn, seq_no=seq_no)

    token_handler_b.validate(request)
    token_handler_b.updateState([txn])
    state_key = TokenReqHandler.create_state_key(VALID_ADDR_1, seq_no)
    key = token_handler_b.utxo_cache._create_type1_key(Output(VALID_ADDR_1, seq_no, 60))
    assert token_handler_b.utxo_cache._store._has_key(key)
    try:
        token_handler_b.state.get(state_key, False)
    except Exception:
        pytest.fail("This state key isn't in the state")
    token_handler_b.onBatchRejected()


def test_token_req_handler_onBatchCreated_success(token_handler_b, node):
    # Empty UTXO Cache
    token_handler_b.onBatchRejected()
    # add output to UTXO Cache
    output = Output(VALID_ADDR_7, 10, 100)
    token_handler_b.utxo_cache.add_output(output)
    state_root = node[1].master_replica.stateRootHash(TOKEN_LEDGER_ID)
    # run onBatchCreated
    token_handler_b.onBatchCreated(state_root)
    # Verify onBatchCreated worked properly
    type1_key = token_handler_b.utxo_cache._create_type1_key(output)
    type2_key = token_handler_b.utxo_cache._create_type2_key(output.address)
    print(token_handler_b.utxo_cache.un_committed)
    assert token_handler_b.utxo_cache.un_committed == [(state_root, OrderedDict([(type1_key, str(output.value)),
                                                                                 (type2_key, str(output.seq_no))]))]


def test_token_req_handler_onBatchRejected_success(token_handler_b):
    token_handler_b._add_new_output(Output(VALID_ADDR_1, 40, 100))
    token_handler_b.onBatchRejected()
    assert token_handler_b.utxo_cache.un_committed == []


def test_token_req_handler_commit_success(public_minting, token_handler_c, node):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "amount": 30
                                                      }, {
                                                          "address": VALID_ADDR_2,
                                                          "amount": 30
                                                      }],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "seqNo": 1
                                                      }],
                                                      SIGS: ['']}, None, SIGNATURES, 1)
    # apply transaction
    state_root = node[2].master_replica.stateRootHash(TOKEN_LEDGER_ID)
    txn_root = node[2].master_replica.txnRootHash(TOKEN_LEDGER_ID)
    token_handler_c.apply(request, CONS_TIME)
    new_state_root = node[2].master_replica.stateRootHash(TOKEN_LEDGER_ID)
    new_txn_root = node[2].master_replica.txnRootHash(TOKEN_LEDGER_ID)
    # add batch
    token_handler_c.onBatchCreated(base58.b58decode(new_state_root.encode()))
    # commit batch
    assert token_handler_c.utxo_cache.get_unspent_outputs(VALID_ADDR_1, True) == [Output(VALID_ADDR_1, 1, 40)]
    assert token_handler_c.utxo_cache.get_unspent_outputs(VALID_ADDR_2, True) == [Output(VALID_ADDR_2, 1, 60)]
    commit_ret_val = token_handler_c.commit(1, new_state_root, new_txn_root, None)
    assert token_handler_c.utxo_cache.get_unspent_outputs(VALID_ADDR_1, True) == [Output(VALID_ADDR_1, 2, 30)]
    assert token_handler_c.utxo_cache.get_unspent_outputs(VALID_ADDR_2, True) == [Output(VALID_ADDR_2, 1, 60),
                                                                                      Output(VALID_ADDR_2, 2, 30)]
    assert new_state_root != state_root
    assert new_txn_root != txn_root


def test_token_req_handler_get_query_response_success(public_minting, token_handler_d):
    data = {TXN_TYPE: GET_UTXO, ADDRESS: VALID_ADDR_1}
    request = Request(VALID_IDENTIFIER, VALID_REQID, data, None, SIGNATURES, 1)
    results = token_handler_d.get_query_response(request)
    state_proof = results.pop(STATE_PROOF)

    assert state_proof
    assert results == {ADDRESS: VALID_ADDR_1, TXN_TYPE: GET_UTXO,
                       OUTPUTS: [Output(address=VALID_ADDR_1, seq_no=1, value=40)],
                       'identifier': VALID_IDENTIFIER, 'reqId': VALID_REQID}


def test_token_req_handler_get_query_response_invalid_txn_type(public_minting, token_handler_d):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: XFER_PUBLIC,
                                                      OUTPUTS: [{
                                                          "address": VALID_ADDR_2,
                                                          "amount": 40}],
                                                      INPUTS: [{
                                                          "address": VALID_ADDR_1,
                                                          "seqNo": 1}]}, None, SIGNATURES, 1)
    # A KeyError is expected because get_query_responses can only handle query transaction types
    with pytest.raises(KeyError):
        token_handler_d.get_query_response(request)


def test_token_req_handler_get_all_utxo_success(public_minting, token_handler_d):
    request = Request(VALID_IDENTIFIER, VALID_REQID,
                      {TXN_TYPE: GET_UTXO, ADDRESS: VALID_ADDR_1},
                      None, SIGNATURES, 1)

    results = token_handler_d.get_query_response(request)
    state_proof = results.pop(STATE_PROOF)

    assert state_proof
    assert results == {ADDRESS: VALID_ADDR_1, TXN_TYPE: GET_UTXO,
                       OUTPUTS: [
                           Output(address=VALID_ADDR_1, seq_no=1, value=40)
                       ],
                       'identifier': VALID_IDENTIFIER, 'reqId': VALID_REQID}


def test_token_req_handler_create_state_key_success(token_handler_d):
    state_key = token_handler_d.create_state_key(VALID_ADDR_1, 40)
    assert state_key.decode() == '{}:40'.format(VALID_ADDR_1)


# This test acts as a test for the static method of sum_inputs too
def test_token_req_handler_sum_inputs_success(public_minting, token_handler_d):
    # Verify no outputs
    pre_add_outputs = token_handler_d.utxo_cache.get_unspent_outputs(VALID_ADDR_4)
    assert pre_add_outputs == []

    # add and verify new unspent output added
    token_handler_d.utxo_cache.add_output(Output(VALID_ADDR_4, 5, 150))
    post_add_outputs = token_handler_d.utxo_cache.get_unspent_outputs(VALID_ADDR_4)
    assert post_add_outputs == [Output(VALID_ADDR_4, 5, 150)]

    # add second unspent output and verify
    token_handler_d.utxo_cache.add_output(Output(VALID_ADDR_4, 6, 100))
    post_second_add_outputs = token_handler_d.utxo_cache.get_unspent_outputs(VALID_ADDR_4)
    assert post_second_add_outputs == [Output(VALID_ADDR_4, 5, 150), Output(VALID_ADDR_4, 6, 100)]

    # Verify sum_inputs is working properly
    request = Request(VALID_IDENTIFIER,
                      VALID_REQID,
                      {
                          TXN_TYPE: XFER_PUBLIC,
                          OUTPUTS: None,
                          INPUTS: [{"address": VALID_ADDR_4, "seqNo": 5}, {"address": VALID_ADDR_4, "seqNo": 6}]
                      },
                      None,
                      SIGNATURES,
                      1)
    sum_inputs = token_handler_d._sum_inputs(request)
    assert sum_inputs == 250


# This test acts as a test for the static method of spent_inputs too
def test_token_req_handler_spend_input_success(public_minting, token_handler_d):
    # add input to address
    token_handler_d.utxo_cache.add_output(Output(VALID_ADDR_5, 7, 200))

    # spend input to address
    token_handler_d._spend_input(VALID_ADDR_5, 7)
    unspent_outputs = token_handler_d.utxo_cache.get_unspent_outputs(VALID_ADDR_5)
    assert unspent_outputs == []


# This test acts as a test for the static method of add_new_output too
def test_token_req_handler_add_new_output_success(token_handler_d):
    token_handler_d._add_new_output(Output(VALID_ADDR_6, 8, 350))
    unspent_outputs = token_handler_d.utxo_cache.get_unspent_outputs(VALID_ADDR_6)
    assert unspent_outputs == [Output(VALID_ADDR_6, 8, 350)]


class TestValidateMintPublic():
    @pytest.fixture(autouse=True)
    def init(self, helpers):
        self.addresses = helpers.wallet.create_new_addresses(2)
        self.handler = helpers.node.get_token_req_handler()

    @pytest.fixture()
    def mint_request(self, helpers):
        outputs = [[address, 1000] for address in self.addresses]
        request = helpers.request.mint(outputs)
        return request

    @pytest.fixture()
    def increased_trustees(self, helpers, trustee_wallets, sdk_wallet_trustee):
        seeds = [randomString(32) for _ in range(3)]

        requests = [
            helpers.request.nym(seed=seed, role=TRUSTEE_STRING)
            for seed in seeds
        ]

        responses = helpers.sdk.send_and_check_request_objects(requests)

        wallets = [helpers.wallet.create_client_wallet(seed) for seed in seeds]

        yield trustee_wallets + wallets

        # TODO: Not certain if this is actually changing the role.
        def _update_nym_standard_user(response):
            data = get_payload_data(response[RESULT])
            request = helpers.request.nym(
                dest=data[TARGET_NYM],
                verkey=data[VERKEY],
                role=None
            )
            return request

        requests = [
            _update_nym_standard_user(response)
            for _, response in responses
        ]

        helpers.sdk.send_and_check_request_objects(requests)

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
        mint_request = helpers.wallet.sign_request(
            mint_request,
            steward_wallets[0:1]
        )
        with pytest.raises(InvalidClientMessageException):
            self.handler.validate(mint_request)

    def test_valid_request(self, helpers, mint_request):
        valid = self.handler.validate(mint_request)
        assert valid is None

    @pytest.mark.skip
    def test_quorum_trustees(self, helpers, mint_request, trustee_wallets):
        mint_request = self.sign_with_quorum(
            helpers,
            mint_request,
            trustee_wallets
        )
        valid = self.handler.validate(mint_request)
        assert valid is None

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
        valid = self.handler.validate(mint_request)
        assert valid is None

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
