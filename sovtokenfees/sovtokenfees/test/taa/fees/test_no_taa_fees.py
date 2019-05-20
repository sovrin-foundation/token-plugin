from sovtokenfees.constants import FEES

from plenum.common.constants import NYM


def test_nym_with_fees_with_taa(helpers,
                                addresses,
                                mint_tokens,
                                fees_set):
    text, version = "test taa", "abc"
    request = helpers.request.nym(taa=True, text=text, version=version, mechanism="aaa")
    utxos = helpers.general.get_utxo_addresses(addresses[:1])[0]
    request = helpers.request.add_fees(
        request,
        utxos,
        fees_set[FEES][NYM],
        change_address=addresses[0]
    )[0]
    helpers.sdk.sdk_send_and_check([request])


def test_nym_with_fees_no_taa(helpers,
                              addresses,
                              mint_tokens,
                              fees_set, ):
    request = helpers.request.nym()
    utxos = helpers.general.get_utxo_addresses(addresses[:1])[0]
    request = helpers.request.add_fees(
        request,
        utxos,
        fees_set[FEES][NYM],
        change_address=addresses[0]
    )[0]
    helpers.sdk.sdk_send_and_check([request])
