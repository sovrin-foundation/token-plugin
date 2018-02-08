import random

import itertools
from collections import defaultdict

import pytest

from plenum.common.util import randomString
from plenum.server.plugin.token.types import Output
from plenum.server.plugin.token.utxo_cache import UTXOCache
from storage.test.conftest import parametrised_storage


@pytest.fixture()             # noqa
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
