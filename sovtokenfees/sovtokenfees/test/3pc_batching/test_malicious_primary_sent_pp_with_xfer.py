import pytest
from plenum.common.exceptions import InvalidClientMessageException, RequestRejectedException
from sovtokenfees.test.helper import get_amount_from_token_txn, send_and_check_transfer

from plenum.common.txn_util import get_seq_no

from plenum.test.test_node import getPrimaryReplica


def test_malicious_primary_sent_pp_with_xfer(looper, helpers,
                                   nodeSetWithIntegratedTokenPlugin,
                                   sdk_pool_handle,
                                   fees_set, address_main, xfer_mint_tokens,
                                   fees, xfer_addresses):
    def raise_invalid_ex():
        raise InvalidClientMessageException(1, 2, 3)

    nodes = nodeSetWithIntegratedTokenPlugin
    current_amount = get_amount_from_token_txn(xfer_mint_tokens)
    malicious_primary = getPrimaryReplica(nodes).node
    not_malicious_nodes = set(nodes) - {malicious_primary}
    seq_no = get_seq_no(xfer_mint_tokens)
    for n in not_malicious_nodes:
        n.master_replica._ordering_service._do_dynamic_validation = lambda *args, **kwargs: raise_invalid_ex()
    with pytest.raises(RequestRejectedException, match="client request invalid"):
        current_amount, seq_no, _ = send_and_check_transfer(helpers, xfer_addresses, fees, looper, current_amount, seq_no)

