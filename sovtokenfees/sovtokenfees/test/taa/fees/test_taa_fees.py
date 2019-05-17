import pytest
from sovtokenfees.constants import FEES

from plenum.common.constants import NYM
from plenum.common.exceptions import RequestRejectedException


def test_nym_with_fees_with_taa(helpers,
                                address_main,
                                addresses,
                                mint_tokens,
                                fees_set,
                                set_acceptance_mechanism,
                                set_transaction_author_agreement):
    text, version = set_transaction_author_agreement
    request = helpers.request.nym(taa=True, text=text, version=version, mechanism=set_acceptance_mechanism)
    utxos = helpers.general.get_utxo_addresses([address_main])[0]
    request = helpers.request.add_fees(
        request,
        utxos,
        fees_set[FEES][NYM],
        change_address=address_main
    )[0]
    helpers.sdk.sdk_send_and_check([request])


@pytest.mark.skip(reason="Will work when validation of TAA is enabled")
def test_nym_with_fees_no_taa(helpers,
                                address_main,
                                addresses,
                                mint_tokens,
                                fees_set,
                                set_acceptance_mechanism,
                                set_transaction_author_agreement):
    request = helpers.request.nym()
    utxos = helpers.general.get_utxo_addresses([address_main])[0]
    request = helpers.request.add_fees(
        request,
        utxos,
        fees_set[FEES][NYM],
        change_address=address_main
    )[0]
    with pytest.raises(RequestRejectedException):
        helpers.sdk.sdk_send_and_check([request])