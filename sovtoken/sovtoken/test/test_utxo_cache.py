import random

import itertools
from collections import defaultdict

import pytest

from plenum.common.util import randomString
from sovtoken.types import Output
from sovtoken.utxo_cache import UTXOCache
from storage.test.conftest import parametrised_storage

# Test Constants
VALID_ADDR_1 = '6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1'
VALID_ADDR_2 = '8kjqqnF3m6agp9auU7k4TWAhuGygFAgPzbNH3shp4HFL'


@pytest.fixture()  # noqa
def utxo_cache(parametrised_storage) -> UTXOCache:
    cache = UTXOCache(parametrised_storage)
    return cache


def gen_outputs(num):
    return [Output(randomString(32), random.randint(1000, 10000),
                   random.randint(100, 500)) for i in range(num)]


def test_add_unspent_output(utxo_cache):
    num_outputs = 5
    outputs = gen_outputs(num_outputs)
    for i in range(num_outputs):
        with pytest.raises(KeyError):
            utxo_cache.get_output(outputs[i], True)
        utxo_cache.add_output(outputs[i], True)
        out = utxo_cache.get_output(outputs[i], True)
        assert out.value == outputs[i].value


def test_spend_unspent_output(utxo_cache):
    num_outputs = 5
    outputs = gen_outputs(num_outputs)
    for i in range(num_outputs):
        utxo_cache.add_output(outputs[i], True)
        new_out = Output(outputs[i].address, outputs[i].seq_no, None)
        utxo_cache.get_output(new_out, True)
        utxo_cache.spend_output(new_out, True)
        with pytest.raises(KeyError):
            utxo_cache.get_output(new_out, True)
        with pytest.raises(KeyError):
            utxo_cache.spend_output(new_out, True)


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
        assert utxo_cache.get_output(output) == output
    except Exception:
        pytest.fail("The output hasn't been added")

    # teardown test
    utxo_cache.reject_batch()


def test_add_outputs_invalid_output(utxo_cache):
    # setup
    invalid_output = (VALID_ADDR_1, 10, 10)
    with pytest.raises(AttributeError):
        utxo_cache.add_output(invalid_output)

    # teardown test
    utxo_cache.reject_batch()


def test_get_output_success(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    utxo_cache.add_output(output)
    try:
        utxo_cache.get_output(output)
    except Exception:
        pytest.fail("One of your outputs has not been added")

    # teardown test
    utxo_cache.reject_batch()


def test_get_output_missing_output(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    with pytest.raises(KeyError):
        utxo_cache.get_output(output)

    # teardown test
    utxo_cache.reject_batch()


def test_get_output_invalid_output(utxo_cache):
    # setup
    invalid_output = (VALID_ADDR_2, 10, 10)
    with pytest.raises(AttributeError):
        utxo_cache.get_output(invalid_output)

    # teardown test
    utxo_cache.reject_batch()


def test_spend_output_success(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    utxo_cache.add_output(output)
    try:
        utxo_cache.spend_output(output)
    except Exception:
        pytest.fail("This output failed to be spent")

    # teardown test
    utxo_cache.reject_batch()


def test_spend_output_invalid_output(utxo_cache):
    invalid_output = (VALID_ADDR_1, 10, 10)
    with pytest.raises(AttributeError):
        utxo_cache.spend_output(invalid_output)

    # teardown test
    utxo_cache.reject_batch()


def test_spend_output_fail_output_not_in_cache(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    with pytest.raises(KeyError):
        utxo_cache.spend_output(output)

    # teardown test
    utxo_cache.reject_batch()


def test_spend_output_double_spend_fail(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    utxo_cache.add_output(output)
    # First spend
    utxo_cache.spend_output(output)

    with pytest.raises(KeyError):
        # Second spend fails as expected
        utxo_cache.spend_output(output)

    # teardown test
    utxo_cache.reject_batch()


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

    # teardown test
    utxo_cache.reject_batch()


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

    # teardown test
    utxo_cache.reject_batch()


def test_create_type1_key(utxo_cache):
    output = Output(VALID_ADDR_1, 10, 10)
    type1_key = utxo_cache._create_type1_key(output)
    assert type1_key == '0:6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1:10'

    # teardown test
    utxo_cache.reject_batch()


def test_create_type1_val_invalid(utxo_cache):
    seqNos = [10, 11, 12, 5, 13, 6]
    with pytest.raises(TypeError):
        type2_val = utxo_cache._create_type2_val(seqNos)

    # teardown test
    utxo_cache.reject_batch()


def test_create_type1_val_success(utxo_cache):
    seqNos = ['10', '11', '12', '5', '13', '6']
    type2_val = utxo_cache._create_type2_val(seqNos)
    assert type2_val == '10:11:12:5:13:6'

    # teardown test
    utxo_cache.reject_batch()


def test_create_type2_key(utxo_cache):
    address = VALID_ADDR_1
    type1_key = utxo_cache._create_type2_key(VALID_ADDR_1)
    assert type1_key == '1:6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1'

    # teardown test
    utxo_cache.reject_batch()


def test_parse_type2_val(utxo_cache):
    type2_val = '10:11:12:5:13:6'
    type2_val_list = utxo_cache._parse_type2_val(type2_val)
    assert type2_val_list == ['10', '11', '12', '5', '13', '6']

    # teardown test
    utxo_cache.reject_batch()


def test_parse_type2_val_invalid_list(utxo_cache):
    type2_val = [10, 11, 12, 5, 13, 6]
    with pytest.raises(AttributeError):
        type2_val_list = utxo_cache._parse_type2_val(type2_val)

    # teardown test
    utxo_cache.reject_batch()


def test_parse_type2_val_invalid_wrong_split(utxo_cache):
    type2_val = '10,11,12,5,13,6'
    type2_val_list = utxo_cache._parse_type2_val(type2_val)
    assert type2_val_list == ['10,11,12,5,13,6']

    # teardown test
    utxo_cache.reject_batch()


def test_parse_type2_val_empty(utxo_cache):
    type2_val = ''
    type2_val_list = utxo_cache._parse_type2_val(type2_val)
    assert type2_val_list == []

    # teardown test
    utxo_cache.reject_batch()
