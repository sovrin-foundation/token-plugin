import json

import pytest
from sovtokenfees.test.helper import get_amount_from_token_txn, nyms_with_fees

from plenum.common.exceptions import InvalidClientMessageException, RequestRejectedException
from plenum.test.test_node import getPrimaryReplica
from plenum.test.helper import sdk_send_signed_requests, sdk_get_and_check_replies


def test_malicious_primary_sent_pp(looper, helpers,
                                   nodeSetWithIntegratedTokenPlugin,
                                   sdk_pool_handle,
                                   fees_set, address_main, mint_tokens):
    def raise_invalid_ex():
        raise InvalidClientMessageException(1,2,3)
    nodes = nodeSetWithIntegratedTokenPlugin
    amount = get_amount_from_token_txn(mint_tokens)
    init_seq_no = 1
    request1, request2 = nyms_with_fees(2,
                                        helpers,
                                        fees_set,
                                        address_main,
                                        amount,
                                        init_seq_no=init_seq_no)
    malicious_primary = getPrimaryReplica(nodes).node
    not_malicious_nodes = set(nodes) - {malicious_primary}
    for n in not_malicious_nodes:
        n.doDynamicValidation = lambda *args, **kwargs: raise_invalid_ex()
    r1 = sdk_send_signed_requests(sdk_pool_handle, [json.dumps(request1.as_dict)])

    with pytest.raises(RequestRejectedException, match="client request invalid"):
        sdk_get_and_check_replies(looper, r1)
