import pytest
from plenum.common.exceptions import InvalidClientMessageException
from stp_core.common.util import adict

from sovtokenfees.constants import FEES
from sovtokenfees.static_fee_req_handler import StaticFeesReqHandler


def test_fees_variations():
    test_fees = [  # valid
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2]
        ],
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj = adict()

    test_obj[FEES] = test_fees
    StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid address type
        [
         [2, 2]
        ],
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid input seqNo
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "2"]
        ],
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
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
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid, No sig
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2]
        ],
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
        ]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # invalid too many OUTPUTS
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2]
        ],
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9], ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = [  # valid - no outputs
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2]
        ],
        [

        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    StaticFeesReqHandler.validate_fees(test_obj)


    test_fees = [  # invalid too many sigs
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2]
        ],
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox", "5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_fees = (  # invalid not list
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2]
        ],
        [
         ["2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 9]
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    )
    test_obj[FEES] = test_fees
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)

    test_obj = "test"
    with pytest.raises(InvalidClientMessageException):
        StaticFeesReqHandler.validate_fees(test_obj)