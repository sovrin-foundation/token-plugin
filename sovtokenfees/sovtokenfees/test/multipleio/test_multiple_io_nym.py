import pytest

from plenum.common.exceptions import RequestNackedException
from indy_common.constants import NYM

from sovtokenfees.constants import MAX_FEE_OUTPUTS

from sovtokenfees.test.constants import NYM_FEES_ALIAS


@pytest.fixture(
    scope='module',
    params=[
        {NYM_FEES_ALIAS: 4},  # with fees
    ], ids=lambda x: 'fees' if x[NYM_FEES_ALIAS] else 'nofees'
)
def fees(request):
    return request.param


def test_nym_with_multiple_io(
    nodeSetWithIntegratedTokenPlugin,
    fees_set,
    mint_multiple_tokens,
    io_addresses,
    prepare_inputs,
    prepare_outputs,
    send_and_check_nym,
):
    def _check():
        inputs = prepare_inputs()
        outputs = prepare_outputs(txn_type=NYM, inputs=inputs)

        if len(outputs) > MAX_FEE_OUTPUTS:
            with pytest.raises(
                RequestNackedException,
                match=(r".*length should be at most {}.*"
                       .format(MAX_FEE_OUTPUTS))
            ):
                send_and_check_nym(inputs, outputs)
        else:
            send_and_check_nym(inputs, outputs)

    _check()
    io_addresses.rotate()
    _check()
