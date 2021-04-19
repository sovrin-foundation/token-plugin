import pytest

from sovtokenfees.messages.fields import TxnFeesField


def _val_to_exception(validation_result):
    if validation_result:
        raise Exception(validation_result)


def test_fees_variations():
    test_fees = [  # valid
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    _val_to_exception(TxnFeesField().validate(test_fees))

    test_fees = [  # invalid address type
        [
            {"address": 2, "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    with pytest.raises(Exception):
        _val_to_exception(TxnFeesField().validate(test_fees))

    test_fees = [  # invalid input seqNo
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": "2"}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    with pytest.raises(Exception):
        _val_to_exception(TxnFeesField().validate(test_fees))

    test_fees = [  # invalid input as tuple
        [
            ("2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", 2)
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    with pytest.raises(Exception):
        _val_to_exception(TxnFeesField().validate(test_fees))

    test_fees = [  # invalid, No sig
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ]
    ]
    with pytest.raises(Exception):
        _val_to_exception(TxnFeesField().validate(test_fees))

    test_fees = [  # invalid too many OUTPUTS
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9},
            {"address": "dctKSXBbv2My3TGGUgTFjkxu1A9JM3Sscd5FydY4dkxnfwA7q", "amount": 9}
        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    with pytest.raises(Exception):
        _val_to_exception(TxnFeesField().validate(test_fees))

    test_fees = [  # valid - no outputs
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "seqNo": 2}
        ],
        [

        ],
        ["5Z7ktpfVQAhj2gMFR8L6JnG7fQQJzqWwqrDgXQP1CYf2vrjKPe2a27borFVuAcQh2AttoejgAoTzJ36wfyKxu5ox"]
    ]
    _val_to_exception(TxnFeesField().validate(test_fees))

    test_fees = [  # invalid - no inputs
        [],
        [
            {"address": "2jS4PHWQJKcawRxdW6GVsjnZBa1ecGdCssn7KhWYJZGTXgL7Es", "amount": 9}
        ],
        []
    ]
    with pytest.raises(Exception):
        _val_to_exception(TxnFeesField().validate(test_fees))

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
    with pytest.raises(Exception):
        _val_to_exception(TxnFeesField().validate(test_fees))
