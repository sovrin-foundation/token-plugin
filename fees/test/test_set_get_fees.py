import pytest

from plenum.common.constants import NYM, STEWARD
from plenum.common.exceptions import RequestNackedException, \
    RequestRejectedException
from plenum.server.plugin.fees.test.helper import get_fees_from_ledger, \
    check_fee_req_handler_in_memory_map_updated, send_set_fees, set_fees
from plenum.server.plugin.token.src.constants import XFER_PUBLIC
from plenum.test.conftest import get_data_for_role
from plenum.server.plugin.token.test.conftest import build_wallets_from_data


def test_get_fees_when_no_fees_set(looper, nodeSetWithIntegratedTokenPlugin,
                                   sdk_wallet_client, sdk_pool_handle):
    assert get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle) == {}
    check_fee_req_handler_in_memory_map_updated(nodeSetWithIntegratedTokenPlugin, {})


def test_trustee_set_invalid_fees(looper, nodeSetWithIntegratedTokenPlugin,
                                  sdk_wallet_client, sdk_pool_handle,
                                  trustee_wallets):
    """
    Fees cannot be negative
    """
    fees = {
        NYM: -1,
        XFER_PUBLIC: 2
    }
    with pytest.raises(RequestNackedException):
        send_set_fees(looper, trustee_wallets, fees, sdk_pool_handle)
    assert get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle) == {}


def test_non_trustee_set_fees(looper, nodeSetWithIntegratedTokenPlugin,
                              sdk_wallet_client, sdk_pool_handle, poolTxnData):
    """
    Only trustees can change the fees
    """
    fees = {
        NYM: 1,
        XFER_PUBLIC: 2
    }
    steward_data = get_data_for_role(poolTxnData, STEWARD)
    steward_wallets = build_wallets_from_data(steward_data)
    with pytest.raises(RequestRejectedException):
        send_set_fees(looper, steward_wallets, fees, sdk_pool_handle)
    assert get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle) == {}


@pytest.fixture(scope="module")
def fees_set(looper, nodeSetWithIntegratedTokenPlugin, sdk_pool_handle,
             trustee_wallets, fees):
    return set_fees(looper, trustee_wallets, fees, sdk_pool_handle)


def test_trustee_set_valid_fees(fees_set, nodeSetWithIntegratedTokenPlugin,
                                fees):
    """
    Set a valid fees
    """
    check_fee_req_handler_in_memory_map_updated(
        nodeSetWithIntegratedTokenPlugin, fees)


def test_get_fees(fees_set, looper, nodeSetWithIntegratedTokenPlugin,
                  sdk_wallet_client, sdk_pool_handle, fees):
    """
    Get the fees from the ledger
    """
    assert get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle) == fees


def test_change_fees(fees_set, looper, nodeSetWithIntegratedTokenPlugin,
                     sdk_wallet_client, sdk_pool_handle, trustee_wallets, fees):
    """
    Change the fees on the ledger and check that fees has changed
    """
    updated_fees = {**fees, NYM: 10}
    set_fees(looper, trustee_wallets, updated_fees, sdk_pool_handle)
    new_fees = get_fees_from_ledger(looper, sdk_wallet_client, sdk_pool_handle)
    assert new_fees == updated_fees
    assert new_fees != fees
    check_fee_req_handler_in_memory_map_updated(nodeSetWithIntegratedTokenPlugin,
                                                updated_fees)
