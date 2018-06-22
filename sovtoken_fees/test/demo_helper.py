import pytest

import json
from plenum.common.constants import NYM
from plenum.server.plugin.sovtoken_fees.test.helper import send_set_fees, get_fees_from_ledger, gen_nym_req_for_fees
from plenum.server.plugin.sovtoken.src.util import update_token_wallet_with_result
from plenum.server.plugin.sovtoken.test.helper import send_public_mint, send_get_utxo
from plenum.test.helper import sdk_send_and_check


@pytest.fixture()
def methods(txnPoolNodeSet, looper, trustee_wallets, fees, sdk_pool_handle, sdk_wallet_client, sdk_wallet_steward):
    return DemoMethods(txnPoolNodeSet, looper, trustee_wallets, fees, sdk_pool_handle, sdk_wallet_client, sdk_wallet_steward)


class DemoMethods:

    def __init__(self, nodes, looper, trustee_wallets, fees, sdk_pool_handle,
                 sdk_wallet_client, sdk_wallet_steward):
        self.nodes = nodes
        self.looper = looper
        self.trustee_wallets = trustee_wallets
        self.fees = fees
        self.sdk_pool_handle = sdk_pool_handle
        self.sdk_wallet_client = sdk_wallet_client
        self.sdk_wallet_steward = sdk_wallet_steward

    def mint_tokens(self, address, tokens):
        outputs = [[address, tokens]]
        (_request, reply) = send_public_mint(self.looper, self.trustee_wallets,
                                             outputs, self.sdk_pool_handle)[0]
        return reply

    def set_fees(self, fees):
        (_request, reply) = send_set_fees(self.looper, self.trustee_wallets,
                                          fees, self.sdk_pool_handle)[0]
        return reply

    def get_fees(self):
        resp = get_fees_from_ledger(self.looper, self.sdk_wallet_client,
                                    self.sdk_pool_handle)
        return resp

    def update_wallet(self, wallet):
        wallet_addresses = list(wallet.addresses.keys())
        for addr in wallet_addresses:
            utxo_resp = send_get_utxo(self.looper, addr,
                                      self.sdk_wallet_client,
                                      self.sdk_pool_handle)
            update_token_wallet_with_result(wallet, utxo_resp)

    def get_utxo_at_wallet_address(self, wallet, address):
        self.update_wallet(wallet)
        return wallet.get_all_wallet_utxos()[address]

    def create_nym_request(self, wallet, fees_address):
        nym_request = gen_nym_req_for_fees(self.looper, self.sdk_wallet_steward)
        fees = self.get_fees()
        return wallet.add_fees_to_request(nym_request, fee_amount=fees[NYM],
                                          address=fees_address.address)

    def send_nym_request(self, nym_request):
        (_request, reply) = sdk_send_and_check(
            [json.dumps(nym_request.__dict__)],
            self.looper,
            None,
            self.sdk_pool_handle, 10)[0]

        return reply

    def get_last_ledger_transaction_on_all_nodes(self, ledger_id):
        transactions = []
        for node in self.nodes:
            ledger = node.getLedger(ledger_id)
            last_sequence_number = ledger.size
            transactions.append(ledger.getBySeqNo(last_sequence_number))

        return transactions

