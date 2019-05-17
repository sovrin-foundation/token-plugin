from sovtoken.constants import ADDRESS, AMOUNT


PROD_ATOM_COUNT = 8000000000 * 100000


def test_prod_minting(helpers,
                      address_main):
    helpers.general.do_mint([
        {ADDRESS: address_main, AMOUNT: PROD_ATOM_COUNT},
    ])
    ledger_utxos = helpers.general.get_utxo_addresses([address_main])[0][0]
    assert ledger_utxos[AMOUNT] == PROD_ATOM_COUNT