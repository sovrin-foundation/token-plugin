import pytest
from plenum.common.exceptions import InvalidClientMessageException
from stp_core.common.util import adict

from sovtokenfees.constants import FEES
from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler


def test_fees_variations():
    test_fees = [  # valid
        [
            {"address":"2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj = adict()

    test_obj[FEES] = test_fees
    StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid address type
        [
            {"address": 2, "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid input seqNo
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": "2"}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid input as tuple
        [
         ("2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2)
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid, No sig
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid too many OUTPUTS
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9},
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # valid - no outputs
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [

        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    StaticFeesReqHandler.validate_fees(test_obj)


    test_fees = [  # invalid too many sigs
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        [
            "5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox",
            "5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"
        ]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = (  # invalid not list
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    )
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_obj = "test"
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)