import pytest

from types import SimpleNamespace

from sovtoken.test.helpers.helper_inner_general import HelperInnerGeneral
from sovtoken.test.helpers.helper_inner_request import HelperInnerRequest
from sovtoken.test.helpers.helper_inner_wallet import HelperInnerWallet

from .helper_general import HelperGeneral
from .helper_node import HelperNode
from .helper_request import HelperRequest
from .helper_sdk import HelperSdk
from .helper_wallet import HelperWallet


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
    helper_node = HelperNode(txn_pool_node_set)
    helper_sdk = HelperSdk(
        looper,
        pool_handle,
        txn_pool_node_set,
        sdk_wallet_steward
    )

    helper_inner_wallet = HelperInnerWallet(
        looper,
        sdk_wallet_client,
        trustee_wallets,
        steward_wallets
    )
    helper_wallet = HelperWallet(
        looper,
        sdk_wallet_client,
        trustee_wallets,
        steward_wallets,
        sdk_wallet_handle,
        sdk_trustees,
        sdk_stewards
    )
    helper_requests = HelperRequest(
        helper_wallet,
        helper_sdk,
        looper,
        sdk_wallet_client,
        sdk_wallet_steward
    )
    helper_general = HelperGeneral(helper_sdk, helper_wallet, helper_requests, helper_node)

    helper_inner_wallet = HelperInnerWallet(
        looper,
        sdk_wallet_client,
        trustee_wallets,
        steward_wallets
    )

    helper_inner_requests = HelperInnerRequest(
        helper_inner_wallet,
        helper_sdk,
        looper,
        sdk_wallet_client,
        sdk_wallet_steward
    )

    helper_inner_general = HelperInnerGeneral(helper_sdk, helper_inner_wallet, helper_inner_requests)

    helpers = {
        'inner': SimpleNamespace(**{
            'general': helper_inner_general,
            'request': helper_inner_requests,
            'wallet': helper_inner_wallet,
        }),
        'general': helper_general,
        'request': helper_requests,
        'wallet': helper_wallet,
        'sdk': helper_sdk,
        'node': helper_node,
    }

    return SimpleNamespace(**helpers)
