import random

import itertools
from collections import defaultdict

import pytest

from plenum.common.util import randomString

from sovtoken.exceptions import UTXOError, UTXONotFound
from sovtoken.types import Output
from sovtoken.utxo_cache import UTXOCache
from storage.test.conftest import parametrised_storage

# Test Constants
VALID_ADDR_1 = '6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1'
VALID_ADDR_2 = '8kjqqnF3m6agp9auU7k4TWAhuGygFAgPzbNH3shp4HFL'


@pytest.yield_fixture()  # noqa
def utxo_cache(parametrised_storage) -> UTXOCache:
    cache = UTXOCache(parametrised_storage)
    yield cache
    cache.reject_batch()


def gen_outputs(num):
    return [Output(randomString(32), random.randint(1000, 10000),
                   random.randint(100, 500)) for i in range(num)]


def test_add_unspent_output(utxo_cache):
    num_outputs = 5
    outputs = gen_outputs(num_outputs)
    for i in range(num_outputs):
        assert utxo_cache.get_unspent_outputs(outputs[i].address, True) == []
        utxo_cache.add_output(outputs[i], True)
        outs = utxo_cache.get_unspent_outputs(outputs[i].address, True)
        assert outputs[i].value in [o.value for o in outs]


# Tests spending unspent outputs
def test_spend_unspent_output(utxo_cache):
    num_outputs = 5
    outputs = gen_outputs(num_outputs)
    for i in range(num_outputs):
        utxo_cache.add_output(outputs[i], True)
        new_out = Output(outputs[i].address, outputs[i].seq_no, None)
        assert utxo_cache.get_unspent_outputs(outputs[i].address, True)
        utxo_cache.spend_output(new_out, True)
        assert utxo_cache.get_unspent_outputs(outputs[i].address, True) == []
        with pytest.raises(UTXOError):
            utxo_cache.spend_output(new_out, True)


# Tests that when outputs are spent before they are added, it fails
def test_spend_unadded_invalid_unspent_output(utxo_cache):
    num_outputs = 5
    outputs = gen_outputs(num_outputs)
    for output in outputs:
        assert utxo_cache.get_unspent_outputs(output.address, True) == []
        with pytest.raises(UTXOError):
            utxo_cache.spend_output(output, True)


def test_get_all_unspent_outputs(utxo_cache):
    num_addresses = 5
    num_outputs_per_address = 4
    address_outputs = gen_outputs(num_addresses)
    all_outputs = list(itertools.chain(*[[Output(ao.address, ao.seq_no * (i + 1),
                                                 ao.value * (i + 1)) for i in
                                          range(num_outputs_per_address)]
                                         for ao in address_outputs]))
    outputs_by_address = defaultdict(set)
    for out in all_outputs:
        outputs_by_address[out.address].add(out)

    for o in all_outputs:
        utxo_cache.add_output(o, True)

    for addr in outputs_by_address:
        assert set(utxo_cache.get_unspent_outputs(addr, True)) == outputs_by_address[addr]

    for addr, outs in outputs_by_address.items():
        while outs:
            out = outs.pop()
            utxo_cache.spend_output(out, True)
            assert set(utxo_cache.get_unspent_outputs(addr, True)) == outs


def test_add_outputs(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    try:
        utxo_cache.add_output(output)
        assert utxo_cache.get_unspent_outputs(output.address) == [output, ]
    except Exception:
        pytest.fail("The output hasn't been added")


def test_add_outputs_invalid_output(utxo_cache):
    # setup
    invalid_output = (VALID_ADDR_1, 10, 10)
    with pytest.raises(UTXOError):
        utxo_cache.add_output(invalid_output)


def test_spend_output_success(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    utxo_cache.add_output(output)
    try:
        utxo_cache.spend_output(output)
    except Exception:
        pytest.fail("This output failed to be spent")


def test_spend_output_invalid_output(utxo_cache):
    invalid_output = (VALID_ADDR_1, 10, 10)
    with pytest.raises(UTXOError):
        utxo_cache.spend_output(invalid_output)


def test_spend_output_fail_output_not_in_cache(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    with pytest.raises(UTXOError):
        utxo_cache.spend_output(output)


def test_spend_output_double_spend_fail(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    utxo_cache.add_output(output)
    # First spend
    utxo_cache.spend_output(output)

    with pytest.raises(UTXOError):
        # Second spend fails as expected
        utxo_cache.spend_output(output)


def test_get_unpsent_outputs_success_uncommited_and_committed(utxo_cache):
    output1_addr1 = Output(VALID_ADDR_1, 10, 10)
    output2_addr1 = Output(VALID_ADDR_1, 11, 10)
    output1_addr2 = Output(VALID_ADDR_2, 10, 10)

    utxo_cache.add_output(output1_addr1)
    utxo_cache.add_output(output2_addr1)
    utxo_cache.add_output(output1_addr2)

    unspent_outputs = utxo_cache.get_unspent_outputs(VALID_ADDR_1, False)
    assert output1_addr1 in unspent_outputs
    assert output2_addr1 in unspent_outputs
    assert output1_addr2 not in unspent_outputs


def test_get_unspent_outputs_invalid_address(utxo_cache):
    uncommitted_output1 = Output(VALID_ADDR_1, 10, 10)
    committed_output1 = Output(VALID_ADDR_1, 11, 100)
    committed_output2 = Output(VALID_ADDR_1, 12, 50)

    utxo_cache.add_output(uncommitted_output1, False)
    utxo_cache.add_output(committed_output1, True)
    utxo_cache.add_output(committed_output2, True)

    unspent_outputs = utxo_cache.get_unspent_outputs(VALID_ADDR_1, True)
    assert committed_output1 in unspent_outputs
    assert committed_output2 in unspent_outputs
    assert uncommitted_output1 not in unspent_outputs


def test_sum_inputs_same_address(utxo_cache):
    output1 = Output(VALID_ADDR_1, 10, 10)
    output2 = Output(VALID_ADDR_1, 11, 100)
    output3 = Output(VALID_ADDR_1, 12, 50)

    for b in (True, False):
        utxo_cache.add_output(output1, b)
        utxo_cache.add_output(output2, b)
        utxo_cache.add_output(output3, b)

        assert utxo_cache.sum_inputs([[VALID_ADDR_1, 10], [VALID_ADDR_1, 11], [VALID_ADDR_1, 12]], b) == 160


def test_sum_inputs_different_addresses(utxo_cache):
    output1 = Output(VALID_ADDR_1, 10, 10)
    output2 = Output(VALID_ADDR_1, 11, 100)
    output3 = Output(VALID_ADDR_2, 11, 50)
    output4 = Output(VALID_ADDR_1, 21, 80)
    output5 = Output(VALID_ADDR_2, 39, 300)

    for b in (True, False):
        utxo_cache.add_output(output1, b)
        utxo_cache.add_output(output2, b)
        utxo_cache.add_output(output3, b)
        utxo_cache.add_output(output4, b)
        utxo_cache.add_output(output5, b)

        assert utxo_cache.sum_inputs([[VALID_ADDR_1, 10], [VALID_ADDR_1, 11], [VALID_ADDR_2, 11],
                                      [VALID_ADDR_1, 21], [VALID_ADDR_2, 39]], b) == 540


def test_create_key(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    key = utxo_cache._create_key(output)
    assert key == '6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1'






