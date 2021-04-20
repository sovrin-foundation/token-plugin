# It is assumed the initial minting will give some tokens to the Sovrin
# Foundation and sovtoken seller platform. From then on, exchange will be
# responsible for giving tokens to "users".
import json

import pytest

from base58 import b58encode_check
from indy.ledger import multi_sign_request
from sovtokenfees.test.helper import get_uncommitted_txns_count_for_pool, get_committed_txns_count_for_pool

from plenum.common.constants import TRUSTEE, DOMAIN_LEDGER_ID
from plenum.common.exceptions import (RequestNackedException,
                                      RequestRejectedException,
                                      PoolLedgerTimeoutException)
from plenum.common.txn_util import get_seq_no
from plenum.common.util import randomString
from sovtoken.test.conftest import build_wallets_from_data
from sovtoken.constants import ADDRESS, AMOUNT, SEQNO, PAYMENT_ADDRESS, TOKEN_LEDGER_ID

from plenum.test.delayers import cDelay
from plenum.test.helper import assertExp
from plenum.test.stasher import delay_rules
from stp_core.loop.eventually import eventually

TOKENAMT = int(1e8)
BILLION = int(1e9)

whitelist = ['Error Value is too big while converting message']


@pytest.fixture
def addresses(helpers):
    return helpers.wallet.create_new_addresses(5)


@pytest.fixture(scope="module")
def wallets_non_existant_dids():
    return build_wallets_from_data([
        ('DID01', 'vdbK9YQGxNHviCOZ7RbOtUgIx9d29XwU'),
        ('DID02', 'sWPSHOH12GEnwLOuQAJgCWBzFER8glUU'),
        ('DID03', 'poIRynSnHJ2JSyBiah7AfXViGPfGcZ7Z'),
        ('DID04', 'X2YlFw7ibYIfyB3A7pIBasy4gWpFNTC6'),
    ])


def test_trustee_invalid_minting(helpers, addresses):
    """
    Trustees trying to mint new tokens using invalid output (negative value),
    txn fails
    """
    [address1, address2, *_] = addresses

    outputs = [{ADDRESS: address1, AMOUNT: -20}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_mint(outputs)

    outputs = [{ADDRESS: address1, AMOUNT: "100"}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_mint(outputs)

    outputs = [{ADDRESS: address1, AMOUNT: 0}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_mint(outputs)

    outputs = [{ADDRESS: address1, AMOUNT: 20.5}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_mint(outputs)

    outputs = [{ADDRESS: address1, AMOUNT: None}, {ADDRESS: address2, AMOUNT: 100}]
    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_mint(outputs)

    outputs = []
    with pytest.raises(RequestNackedException, match="Outputs for a mint request can't be empty."):
        helpers.inner.general.do_mint(outputs)


# What about endorsers, TGB, do those fail as well?
def test_non_trustee_minting(helpers, addresses):
    """
    Non trustees (stewards in this case) should not be able to mint new tokens
    """
    [address1, address2, *_] = addresses
    outputs = [{ADDRESS: address1, AMOUNT: 100}, {ADDRESS: address2, AMOUNT: 60}]
    request = helpers.request.mint(outputs)
    request.signatures = {}
    request._identifier = helpers.wallet._stewards[0]
    request = json.dumps(request.as_dict)
    request = helpers.wallet.sign_request_stewards(request)
    request = json.loads(request)
    sigs = request["signatures"]
    request = helpers.sdk.sdk_json_to_request_object(request)
    setattr(request, "signatures", sigs)
    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


# where are the trustee signatures coming from? How is the trustee wallet
# created here?
# who can set the number of trustees needed, where is that value configured?
# Is there a mint limit?
def test_less_than_min_trustee_minting(helpers, addresses, trustee_wallets):
    """
    Less than the required number of trustees participate in minting,
    hence the txn fails
    """
    [address1, address2, *_] = addresses
    outputs = [{ADDRESS: address1, AMOUNT: 100}, {ADDRESS: address2, AMOUNT: 60}]
    request = helpers.request.mint(outputs)
    # Remove one signature.
    for idr in dict(request.signatures):
        if idr != request.identifier:
            request.signatures.pop(idr)
            break
    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_more_than_min_trustee(capsys, helpers, addresses):
    """
    Should be able to mint with more than the minimum number of trustees.
    """
    [address1, *_] = addresses
    outputs = [{ADDRESS: address1, AMOUNT: 100}]
    request = helpers.request.mint(outputs)
    request = helpers.wallet.sign_request_trustees(json.dumps(request.as_dict), number_signers=4)

    request = json.loads(request)
    sigs = request["signatures"]
    request = helpers.sdk.sdk_json_to_request_object(request)
    setattr(request, "signatures", sigs)

    result = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(result)

    [address1_utxos, *_] = helpers.general.get_utxo_addresses(addresses)

    assert address1_utxos[0][PAYMENT_ADDRESS] == address1
    assert address1_utxos[0][AMOUNT] == 100


def test_stewards_with_trustees(helpers, addresses, trustee_wallets, steward_wallets):
    [address1, address2, *_] = addresses

    outputs = [{ADDRESS: address1, AMOUNT: 1000}, {ADDRESS: address2, AMOUNT: 1000}]
    request = helpers.request.mint(outputs)

    # Remove 1 Trustees' signature, assumption is that there were exactly the number of trustees required
    for idr in dict(request.signatures):
        if idr != request.identifier:
            request.signatures.pop(idr)
            break
    # Add a steward in place of the removed Trustee
    request = json.dumps(request.as_dict)
    request = helpers.wallet.sign_request_stewards(request, number_signers=1)
    request = json.loads(request)
    signatures = request["signatures"]
    request = helpers.sdk.sdk_json_to_request_object(request)
    setattr(request, "signatures", signatures)
    with pytest.raises(RequestRejectedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_non_existant_did_with_trustees(
    helpers,
    addresses,
    wallets_non_existant_dids
):
    [address1, address2, *_] = addresses
    signing_wallets = wallets_non_existant_dids[0:1]

    outputs = [{ADDRESS: address1, AMOUNT: 1000}, {ADDRESS: address2, AMOUNT: 1000}]
    request = helpers.request.mint(outputs)
    request = helpers.wallet.sign_request(request, signing_wallets)

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_non_existant_dids(helpers, addresses, wallets_non_existant_dids):
    [address1, address2, *_] = addresses

    outputs = [{ADDRESS: address1, AMOUNT: 1000}, {ADDRESS: address2, AMOUNT: 1000}]
    request = helpers.request.mint(outputs)

    request.signatures = {}
    request = helpers.wallet.sign_request(request, wallets_non_existant_dids)

    with pytest.raises(RequestNackedException):
        helpers.sdk.send_and_check_request_objects([request])


def test_invalid_address(helpers, addresses):
    """
    Minting fails when address is incorrect format.
    """

    def _update_char(s, index, func):
        return s[:index] + func(s[index]) + s[index + 1:]

    def _test_invalid_address(address):
        outputs = [{ADDRESS: address, AMOUNT: 100}]

        with pytest.raises(RequestNackedException):
            helpers.inner.general.do_mint(outputs)

    valid_address = addresses[0]
    invalid_address_length = b58encode_check(randomString(33).encode()).decode()
    invalid_address_character = _update_char(valid_address, 2, lambda _: '!')
    invalid_address_checksum = _update_char(
        valid_address,
        2,
        lambda c: 'B' if c == 'A' else 'A'
    )

    _test_invalid_address(invalid_address_length)
    _test_invalid_address(invalid_address_character)
    _test_invalid_address(invalid_address_checksum)


def test_trustee_valid_minting(helpers, addresses):
    """
    Trustees should mint new tokens increasing the balance of `SF_MASTER`
    and seller_address
    """
    [address1, address2, *_] = addresses
    total_mint = 10 * BILLION * TOKENAMT
    sf_master_gets = 6 * BILLION * TOKENAMT
    remaining = total_mint - sf_master_gets
    outputs = [{ADDRESS: address1, AMOUNT: sf_master_gets}, {ADDRESS: address2, AMOUNT: remaining}]
    result = helpers.general.do_mint(outputs)

    [
        address1_utxos,
        address2_utxos
    ] = helpers.general.get_utxo_addresses([address1, address2])

    assert address1_utxos[0][PAYMENT_ADDRESS] == address1
    assert address1_utxos[0][AMOUNT] == sf_master_gets
    assert address2_utxos[0][PAYMENT_ADDRESS] == address2
    assert address2_utxos[0][AMOUNT] == remaining


def test_two_mints_to_same_address(addresses, helpers):
    outputs = [{ADDRESS: address, AMOUNT: 100} for address in addresses]
    first_mint_result = helpers.general.do_mint(outputs)
    outputs = [{ADDRESS: address, AMOUNT: 200} for address in addresses]
    second_mint_result = helpers.general.do_mint(outputs)
    first_mint_seq_no = get_seq_no(first_mint_result)
    second_mint_seq_no = get_seq_no(second_mint_result)

    [address1, address2, address3, address4, address5] = addresses

    [
        address1_utxos,
        address2_utxos,
        address3_utxos,
        address4_utxos,
        address5_utxos
    ] = helpers.general.get_utxo_addresses(addresses)

    assert first_mint_seq_no != second_mint_seq_no

    assert address1_utxos[0][PAYMENT_ADDRESS] == address1
    assert address1_utxos[0][AMOUNT] == 100
    assert address1_utxos[1][PAYMENT_ADDRESS] == address1
    assert address1_utxos[1][AMOUNT] == 200
    assert address2_utxos[0][PAYMENT_ADDRESS] == address2
    assert address2_utxos[0][AMOUNT] == 100
    assert address2_utxos[1][PAYMENT_ADDRESS] == address2
    assert address2_utxos[1][AMOUNT] == 200
    assert address3_utxos[0][PAYMENT_ADDRESS] == address3
    assert address3_utxos[0][AMOUNT] == 100
    assert address3_utxos[1][PAYMENT_ADDRESS] == address3
    assert address3_utxos[1][AMOUNT] == 200
    assert address4_utxos[0][PAYMENT_ADDRESS] == address4
    assert address4_utxos[0][AMOUNT] == 100
    assert address4_utxos[1][PAYMENT_ADDRESS] == address4
    assert address4_utxos[1][AMOUNT] == 200
    assert address5_utxos[0][PAYMENT_ADDRESS] == address5
    assert address5_utxos[0][AMOUNT] == 100
    assert address5_utxos[1][PAYMENT_ADDRESS] == address5
    assert address5_utxos[1][AMOUNT] == 200


def test_mint_duplicate_address_single_mint(helpers, addresses):
    """
    Can't mint with duplicate address.
    """

    [address1, address2, *_] = addresses
    outputs = [
        {ADDRESS: address1, AMOUNT: 100},
        {ADDRESS: address2, AMOUNT: 100},
        {ADDRESS: address1, AMOUNT: 100}
    ]

    with pytest.raises(RequestNackedException):
        helpers.inner.general.do_mint(outputs)


def test_repeat_mint(helpers, addresses):
    """
    Can't use the same mint request twice.
    """
    address = addresses[0]
    outputs = [{ADDRESS: address, AMOUNT: 100}]
    request = helpers.request.mint(outputs)

    helpers.sdk.send_and_check_request_objects([request])
    helpers.sdk.send_and_check_request_objects([request])

    utxos = helpers.general.get_utxo_addresses([address])[0]

    assert utxos[0][PAYMENT_ADDRESS] == address
    assert utxos[0][AMOUNT] == 100


def test_different_mint_amounts(helpers):
    i64 = 9223372036854775807

    def assert_valid_minting(helpers, amount):
        address = helpers.wallet.create_address()
        outputs = [{ADDRESS: address, AMOUNT: amount}]
        helpers.general.do_mint(outputs)
        helpers.general.get_utxo_addresses([address])[0]

    # 1 sovatom
    assert_valid_minting(helpers, 1)

    # 10 billion tokens
    assert_valid_minting(helpers, 10 * BILLION * TOKENAMT)

    # i64 max sovatoms.
    assert_valid_minting(helpers, i64)

    # ujson has a limit at deserializing i64.
    with pytest.raises(PoolLedgerTimeoutException):
        assert_valid_minting(helpers, i64 + 1)


def test_mint_by_uncommitted_trustee(capsys, looper, nodeSetWithIntegratedTokenPlugin, sdk_wallet_trustee,
                                     helpers, addresses):
    """
    Check that a Trustee not committed yet can sign a MINT txn.
    """
    uncommitted_size_before_domain = get_uncommitted_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                                         DOMAIN_LEDGER_ID)
    uncommitted_size_before_token = get_uncommitted_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                                        TOKEN_LEDGER_ID)
    committed_size_before_domain = get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                                     DOMAIN_LEDGER_ID)
    committed_size_before_token = get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                                    TOKEN_LEDGER_ID)

    node_stashers = [n.nodeIbStasher for n in nodeSetWithIntegratedTokenPlugin]
    with delay_rules(node_stashers, cDelay()):
        # Add a new TRUSTEE (uncommitted)
        new_did, verkey = helpers.wallet.create_did(sdk_wallet=sdk_wallet_trustee)
        req = helpers.request.nym(sdk_wallet=sdk_wallet_trustee,
                                  alias="new_steward",
                                  role=TRUSTEE,
                                  dest=new_did,
                                  verkey=verkey)
        helpers.sdk.send_request_objects([req], wallet=sdk_wallet_trustee)
        looper.run(eventually(
            lambda: assertExp(
                get_uncommitted_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                    DOMAIN_LEDGER_ID) == uncommitted_size_before_domain + 1
            )))
        looper.run(eventually(
            lambda: assertExp(
                get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                  DOMAIN_LEDGER_ID) == committed_size_before_domain
            )))

        # Do mint with a newly added Trustee
        [address1, *_] = addresses
        outputs = [{ADDRESS: address1, AMOUNT: 100}]
        request = helpers.request.mint(outputs, number_signers=2)
        request = looper.loop.run_until_complete(
            multi_sign_request(sdk_wallet_trustee[0], new_did, json.dumps(request.as_dict)))

        request = json.loads(request)
        sigs = request["signatures"]
        request = helpers.sdk.sdk_json_to_request_object(request)
        setattr(request, "signatures", sigs)
        helpers.sdk.send_request_objects([request])

        # make sure we have both txns uncommitted
        looper.run(eventually(
            lambda: assertExp(
                get_uncommitted_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                    DOMAIN_LEDGER_ID) == uncommitted_size_before_domain + 1
            )))
        looper.run(eventually(
            lambda: assertExp(
                get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                  DOMAIN_LEDGER_ID) == committed_size_before_domain
            )))
        looper.run(eventually(
            lambda: assertExp(
                get_uncommitted_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                    TOKEN_LEDGER_ID) == uncommitted_size_before_token + 1
            )))
        looper.run(eventually(
            lambda: assertExp(
                get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                                  TOKEN_LEDGER_ID) == committed_size_before_token
            )))

    # make sure we have both txns committed
    looper.run(eventually(
        lambda: assertExp(
            get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                              DOMAIN_LEDGER_ID) == committed_size_before_domain + 1
        )))
    looper.run(eventually(
        lambda: assertExp(
            get_committed_txns_count_for_pool(nodeSetWithIntegratedTokenPlugin,
                                              TOKEN_LEDGER_ID) == committed_size_before_token + 1
        )))

    [address1_utxos, *_] = helpers.general.get_utxo_addresses(addresses)
    assert address1_utxos[0][PAYMENT_ADDRESS] == address1
    assert address1_utxos[0][AMOUNT] == 100
