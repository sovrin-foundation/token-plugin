import pytest

from types import SimpleNamespace
from .helper_sdk import HelperSdk


def form_helpers(txn_pool_node_set, looper, pool_handle):
    helper_sdk = HelperSdk(looper, pool_handle, txn_pool_node_set)

    helpers = {
        'sdk': helper_sdk
    }

    return SimpleNamespace(**helpers)
