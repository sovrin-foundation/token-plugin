from sovtoken.constants import ADDRESS, AMOUNT

sovatom = 1
sovatoms_in_token = 10 ** 8 * sovatom
# 1 billion
TOKENS_COUNT = 10 ** 9
PROD_ATOM_COUNT = 8 * TOKENS_COUNT * sovatoms_in_token


def test_prod_minting(helpers,
                      address_main):
    helpers.general.do_mint([
        {ADDRESS: address_main, AMOUNT: PROD_ATOM_COUNT},
    ])
    ledger_utxos = helpers.general.get_utxo_addresses([address_main])[0][0]
    assert ledger_utxos[AMOUNT] == PROD_ATOM_COUNT
