import pytest

from types import SimpleNamespace
from .helper_sdk import HelperSdk
from .helper_requests import HelperRequests


def form_helpers(txn_pool_node_set, looper, pool_handle):
    helper_sdk = HelperSdk(looper, pool_handle, txn_pool_node_set)
    helper_requests = HelperRequests(helper_sdk)

    helpers = {
        'sdk': helper_sdk,
        'requests': helper_requests,
    }

    return SimpleNamespace(**helpers)
