import pytest
from sovtokenfees.constants import FEES

from plenum.common.exceptions import RequestRejectedException
from sovtokenfees.test.constants import NYM_FEES_ALIAS


def test_nym_with_fees_with_taa(helpers,
                                addresses,
                                mint_tokens_no_taa,
                                fees_set):
    text, version = "test taa", "abc"
    request = helpers.request.nym(taa=True, text=text, version=version, mechanism="aaa")
    utxos = helpers.general.get_utxo_addresses(addresses[:1])[0]
    request = helpers.request.add_fees(
        request,
        utxos,
        fees_set[FEES][NYM_FEES_ALIAS],
        change_address=addresses[0]
    )[0]
    with pytest.raises(RequestRejectedException):
        helpers.sdk.sdk_send_and_check([request])


def test_nym_with_fees_no_taa(helpers,
                              addresses,
                              mint_tokens_no_taa,
                              fees_set, ):
    request = helpers.request.nym()
    utxos = helpers.general.get_utxo_addresses(addresses[:1])[0]
    request = helpers.request.add_fees(
        request,
        utxos,
        fees_set[FEES][NYM_FEES_ALIAS],
        change_address=addresses[0]
    )[0]
    helpers.sdk.sdk_send_and_check([request])
