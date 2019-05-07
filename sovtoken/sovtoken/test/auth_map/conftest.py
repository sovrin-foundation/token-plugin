import json

import pytest
from indy.did import create_and_store_my_did
from sovtoken.test.wallet import Address

from plenum.common.util import randomString
from plenum.test.pool_transactions.helper import sdk_add_new_nym


@pytest.fixture()
def addresses(helpers, new_client_wallet):
    return [new_client_wallet[2]] + helpers.wallet.create_new_addresses(4)


@pytest.fixture()
def new_client_wallet(looper, sdk_pool_handle,
                      sdk_wallet_trustee, helpers):
    seed = randomString(32)
    alias = "name"
    did, verkey = looper.loop.run_until_complete(
        create_and_store_my_did(sdk_wallet_trustee[0], json.dumps({'seed': seed})))

    wh, did = sdk_add_new_nym(looper, sdk_pool_handle,
                              sdk_wallet_trustee, dest=did,
                              verkey=verkey, alias=alias)
    new_address = Address(seed=seed.encode())
    helpers.wallet.address_map[new_address.address] = new_address
    return wh, did, new_address.address
