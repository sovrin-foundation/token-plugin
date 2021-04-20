import json

import pytest
from indy.did import create_and_store_my_did
from indy.ledger import build_nym_request

from indy_common.authorize.auth_actions import ADD_PREFIX
from indy_common.authorize.auth_constraints import AuthConstraint, OFF_LEDGER_SIGNATURE, AuthConstraintOr
from indy_common.constants import CONSTRAINT
from indy_node.test.helper import build_auth_rule_request_json, sdk_send_and_check_req_json
from sovtoken.constants import AMOUNT
from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no
from sovtokenfees.constants import FEES_FIELD_NAME
from sovtokenfees.test.constants import txn_type_to_alias
from sovtokenfees.test.helper import get_amount_from_token_txn, add_fees_request_with_address

from indy_common.types import Request
from plenum.common.constants import ROLE, VERKEY, NYM, TRUSTEE
from plenum.common.types import OPERATION
from plenum.common.util import randomString
from plenum.server.request_handlers.utils import get_nym_details
from plenum.test.pool_transactions.helper import sdk_add_new_nym

NEW_ROLE = None


@pytest.fixture(scope='function')
def nym_txn_data(looper, sdk_wallet_client):
    seed = randomString(32)

    wh, _ = sdk_wallet_client
    sender_did, sender_verkey = \
        looper.loop.run_until_complete(create_and_store_my_did(wh, json.dumps({'seed': seed})))
    return wh, randomString(5), sender_did, sender_verkey


@pytest.fixture(scope='function')
def changed_auth_rule(looper, sdk_pool_handle, sdk_wallet_trustee, fees_set):
    constraint = AuthConstraintOr(auth_constraints=[AuthConstraint(role='*',
                                                                   sig_count=1,
                                                                   off_ledger_signature=True,
                                                                   metadata={FEES_FIELD_NAME: txn_type_to_alias[NYM]}),
                                                    AuthConstraint(role=TRUSTEE, sig_count=1)
                                                    ])

    req = build_auth_rule_request_json(
        looper, sdk_wallet_trustee[1],
        auth_action=ADD_PREFIX,
        auth_type=NYM,
        field=ROLE,
        old_value=None,
        new_value=NEW_ROLE,
        constraint=constraint.as_dict
    )

    req = json.loads(req)
    req[OPERATION][CONSTRAINT]['auth_constraints'][0][OFF_LEDGER_SIGNATURE] = True
    req = json.dumps(req)

    sdk_send_and_check_req_json(looper, sdk_pool_handle, sdk_wallet_trustee, req)


def test_create_did_without_endorser_payment(looper, nodeSetWithIntegratedTokenPlugin, nym_txn_data, sdk_pool_handle,
                                             fees_set, address_main, mint_tokens, changed_auth_rule,
                                             sdk_wallet_trustee, helpers):
    sdk_add_new_nym(looper, sdk_pool_handle, sdk_wallet_trustee)

    wh, alias, sender_did, sender_verkey = nym_txn_data
    req = looper.loop.run_until_complete(
        build_nym_request(sender_did, sender_did, sender_verkey, alias, NEW_ROLE))

    amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1
    utxos = [{"source": utxo_from_addr_and_seq_no(address_main, init_seq_no),
              AMOUNT: amount}]
    req = Request(**json.loads(req))
    req = add_fees_request_with_address(
        helpers,
        fees_set,
        req,
        address_main,
        utxos=utxos
    )

    helpers.sdk.send_and_check_request_objects([req], wallet=(wh, sender_did))

    details = get_nym_details(nodeSetWithIntegratedTokenPlugin[0].states[1], sender_did, is_committed=True)
    assert details[ROLE] == NEW_ROLE
    assert details[VERKEY] == sender_verkey
