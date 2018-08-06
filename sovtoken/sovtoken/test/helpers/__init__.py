import pytest

from types import SimpleNamespace
from .helper_general import HelperGeneral
from .helper_request import HelperRequest
from .helper_sdk import HelperSdk
from .helper_wallet import HelperWallet


def form_helpers(
    txn_pool_node_set,
    looper, pool_handle,
    trustees,
    sdk_wallet_client
):
    (_client_wallet_handle, client_did) = sdk_wallet_client

    helper_sdk = HelperSdk(looper, pool_handle, txn_pool_node_set)
    helper_wallet = HelperWallet(trustees)
    helper_requests = HelperRequest(
        helper_wallet,
        client_did
    )
    helper_general = HelperGeneral(helper_sdk, helper_wallet, helper_requests)

    helpers = {
        'request': helper_requests,
        'sdk': helper_sdk,
        'wallet': helper_wallet,
        'general': helper_general,
    }

    return SimpleNamespace(**helpers)
