import pytest

from types import SimpleNamespace

import sovtoken
from sovtokenfees.test.helpers.helper_wallet import HelperWallet
from sovtoken.test.helpers.helper_sdk import HelperSdk

from sovtoken.test.helpers.helper_inner_wallet import HelperInnerWallet
from sovtokenfees.test.helpers.helper_request_inner import HelperInnerRequest

from .helper_request import HelperRequest
from .helper_general import HelperGeneral
from .helper_node import HelperNode


# TODO: Have a way to setup helpers between sovtoken and sovtokenfees with less
# repetition.
def form_helpers(
    txn_pool_node_set,
    looper,
    pool_handle,
    trustee_wallets,
    steward_wallets,
    sdk_wallet_client,
    sdk_wallet_steward,
    sdk_wallet_handle,
    sdk_trustees,
    sdk_stewards
):
    helper_wallet = HelperWallet(
        looper,
        sdk_wallet_client,
        trustee_wallets,
        steward_wallets,
        sdk_wallet_handle,
        sdk_trustees,
        sdk_stewards
    )

    helper_inner_wallet = HelperInnerWallet(
        looper,
        sdk_wallet_client,
        trustee_wallets,
        steward_wallets
    )
    helper_node = HelperNode(txn_pool_node_set)
    helper_sdk = HelperSdk(
        looper,
        pool_handle,
        txn_pool_node_set,
        sdk_wallet_steward
    )
    helper_requests_inner = HelperInnerRequest(
        helper_inner_wallet,
        helper_sdk,
        looper,
        sdk_wallet_client,
        sdk_wallet_steward
    )
    helper_requests = HelperRequest(
        helper_wallet,
        helper_sdk,
        looper,
        sdk_wallet_client,
        sdk_wallet_steward
    )

    helper_general = type("HelperGeneral", (
        HelperGeneral,
        sovtoken.test.helpers.helper_general.HelperGeneral,
    ), {})(helper_sdk, helper_wallet, helper_requests, helper_node)
    helper_general_inner = type("HelperInnerGeneral", (
        HelperGeneral,
        sovtoken.test.helpers.helper_inner_general.HelperInnerGeneral,
    ), {})(helper_sdk, helper_inner_wallet, helper_requests_inner)

    helpers = {
        'request': helper_requests,
        'sdk': helper_sdk,
        'wallet': helper_wallet,
        'general': helper_general,
        'node': helper_node,
        'inner': SimpleNamespace(**{
            'wallet': helper_inner_wallet,
            'request': helper_requests_inner,
            'general': helper_general_inner
        })
    }

    helpers = SimpleNamespace(**helpers)

    return helpers