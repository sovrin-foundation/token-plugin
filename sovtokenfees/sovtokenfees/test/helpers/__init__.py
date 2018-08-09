import pytest

from types import SimpleNamespace
from sovtoken.test.helpers.helper_sdk import HelperSdk
from sovtoken.test.helpers.helper_wallet import HelperWallet

from .helper_request import HelperRequest
from .helper_general import HelperGeneral

# TODO: Have a way to setup helpers between sovtoken and sovtokenfees with less
# repetition.
def form_helpers(
    txn_pool_node_set,
    looper,
    pool_handle,
    trustees,
    sdk_wallet_client,
    sdk_wallet_steward,
):
    helper_sdk = HelperSdk(
        looper,
        pool_handle,
        txn_pool_node_set,
        sdk_wallet_steward
    )
    helper_wallet = HelperWallet(trustees)
    helper_requests = HelperRequest(
        helper_wallet,
        helper_sdk,
        looper,
        sdk_wallet_client,
        sdk_wallet_steward
    )
    helper_general = HelperGeneral(helper_sdk, helper_wallet, helper_requests)

    helpers = {
        'request': helper_requests,
        'sdk': helper_sdk,
        'wallet': helper_wallet,
        'general': helper_general,
    }

    return SimpleNamespace(**helpers)
