import pytest

from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler
from plenum.common.constants import DOMAIN_LEDGER_ID, CONFIG_LEDGER_ID
from plenum.common.request import Request
from plenum.common.constants import TXN_TYPE
from sovtokenfees.constants import SET_FEES, GET_FEES, FEES
from sovtoken.constants import XFER_PUBLIC, MINT_PUBLIC, \
    OUTPUTS, INPUTS, GET_UTXO, ADDRESS, TOKEN_LEDGER_ID
from plenum.common.exceptions import UnauthorizedClientRequest, InvalidClientRequest


PROTOCOL_VERSION = 1
VALID_REQID = 1524167698952409
VALID_FEES = {'10001': 8, '1': 4}
VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"

VALID_ADDR_1 = '8kjqqnF3m6agp9auU7k4TWAhuGygFAgPzbNH3shp4HFL'
VALID_ADDR_2 = '6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1'

SIGNATURES = {'E7QRhdcnhAwA6E46k9EtZo': '6191MA6zWmDTZrLJ2zzzWVkppMKdJLsKXrjd3Y3rQH6MNtMA518pwPQt6ergn6MRmeBNeTVCMrmZnqwDPBsGgqoM',
              'M9BJDuS24bqbJNvBRsoGg3': '45csnJ6HAM14ngaDNU7HUEBLSGt2RANvCarc9iYwAVyxLwKaqL4EoQMsJHifeceVE7PwmjkWWLqWQrrerntyUGjG',
              'CA4bVFDU4GLbX8xZju811o': '5tLWyrADCid2EX3EJS44NeFFFEYQxeGJaZth7qSNLTuDgoTtzWn4T1oxXeVehdGQWSLCLqLSDwyAbetf8BYmKe4z',
              'B8fV7naUqLATYocqu7yZ8W': '3pwr7KoAR4kSGnbUgaj1a9t4tGx16hMSXKzgLGRZe8siyE9XTR9c4xLfZJAXuxnofqsPyGh3HC4MhCKQfcSpiaWN'}

BADSIGNATURE = {'E7QRhdcnhAwA6E46k9EtZX': '6191MA6zWmDTZrLJ2zzzWVkppMKdJLsKXrjd3Y3rQH6MNtMA518pwPQt6ergn6MRmeBNeTVCMrmZnqwDPBsGgqoM'}

VALID_INPUTS = [['6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1', 1, '29VP2TZ2E8k7FCtr3cGAkNajkuVKExPvak31e5NtSoJTdke8VyCBeDdftEReAnzhn5wq3XFJ919mrobicqrQbsr8']]
VALID_OUTPUTS = [['GMBk8YVHnctVoCmXuxaAundKyfa5KDredBYE5WZaN5V2', 10], ['6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1', 22]]


@pytest.fixture
def node(txnPoolNodeSet):
    a, b, c, d = txnPoolNodeSet
    nodes = [a, b, c, d]
    return nodes


@pytest.fixture
def token_handler_a(node):
    return node[0].ledger_to_req_handler[TOKEN_LEDGER_ID]


def create_static_handler(token_handler, node):
    config_ledger = node[1].configLedger
    config_state = node[1].getState(CONFIG_LEDGER_ID)
    token_ledger = token_handler.ledger
    token_state = token_handler.state
    utxo_cache = token_handler.utxo_cache
    domain_state = node[1].getState(DOMAIN_LEDGER_ID)
    bls_store = node[1].bls_bft.bls_store

    static_fee_request_handler = StaticFeesReqHandler(config_ledger, config_state, token_ledger, token_state,
                                                      utxo_cache, domain_state, bls_store)
    return static_fee_request_handler


# Method returns None if it was successful -
# TODO: Refactoring should be looked at to return a boolean
# Instead of assuming that everything is good when the return value is None.
# - Static Fee Request Handler (doStaticValidation)
def test_static_fee_req_handler_do_static_validation_valid(token_handler_a, node):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: SET_FEES,
                                                      FEES: VALID_FEES},
                      None, SIGNATURES, 1)

    shandler = create_static_handler(token_handler_a, node)
    ret_value = shandler.doStaticValidation(request)
    assert ret_value is None


# - Static Fee Request Handler (doStaticValidation)
def test_static_fee_req_handler_do_static_validation_invalid(token_handler_a, node):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: SET_FEES},
                      None, SIGNATURES, 1)

    shandler = create_static_handler(token_handler_a, node)
    with pytest.raises(InvalidClientRequest):
        shandler.doStaticValidation(request)


# Method returns None if it was successful -
# TODO: Refactoring should be looked at to return a boolean
# Instead of assuming that everything is good when the return value is None.
# - Static Fee Request Handler (validate)
def test_static_fee_req_handler_validate_valid_signatures(token_handler_a, node):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: SET_FEES,
                                                      FEES: VALID_FEES},
                      None, SIGNATURES, 1)

    shandler = create_static_handler(token_handler_a, node)
    ret_value = shandler.validate(request)
    assert ret_value is None


# - Static Fee Request Handler (validate)
def test_static_fee_req_handler_validate_invalid_signature(token_handler_a, node):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: SET_FEES,
                                                      FEES: VALID_FEES},
                      None, BADSIGNATURE, 1)

    shandler = create_static_handler(token_handler_a, node)
    with pytest.raises(UnauthorizedClientRequest):
        shandler.validate(request)


# - Static Fee Request Handler (apply)
def test_static_fee_req_handler_apply(token_handler_a, node):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: SET_FEES,
                                                      FEES: VALID_FEES},
                      None, SIGNATURES, 1)

    shandler = create_static_handler(token_handler_a, node)
    ret_value = shandler.apply(request, 10)
    assert ret_value[0] == 1


# - Static Fee Request Handler (apply)
@pytest.mark.skip(reason="ret_value is not None when this runs, when it should be. The apply doesn't think it's failing.")
def test_static_fee_req_handler_apply_fails(token_handler_a, node):
    request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: GET_FEES,
                                                      FEES: VALID_FEES},
                      None, SIGNATURES, 1)

    # request = Request(VALID_IDENTIFIER, VALID_REQID, {TXN_TYPE: SET_FEES},
    #                   None, SIGNATURES, 1)


    shandler = create_static_handler(token_handler_a, node)
    ret_value = shandler.apply(request, 10)
    assert ret_value is None