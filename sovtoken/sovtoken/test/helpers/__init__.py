import pytest

from types import SimpleNamespace
from .helper_sdk import HelperSdk
from .helper_request import HelperRequest
from .helper_wallet import HelperWallet


def form_helpers(txn_pool_node_set, looper, pool_handle, trustees):
    helper_sdk = HelperSdk(looper, pool_handle, txn_pool_node_set)
    helper_wallet = HelperWallet(trustees)
    helper_requests = HelperRequest(helper_wallet)

    helpers = {
        'request': helper_requests,
        'sdk': helper_sdk,
        'wallet': helper_wallet,
    }

    return SimpleNamespace(**helpers)
