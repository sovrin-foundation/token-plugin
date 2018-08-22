from collections import defaultdict
from typing import List, Dict, Set

from sovtoken.exceptions import UTXONotFound, UTXOAlreadySpentError, UTXOError, AddressNotFound
from sovtoken.types import Output
from storage.kv_store import KeyValueStorage
from storage.optimistic_kv_store import OptimisticKVStore
from stp_core.common.log import getlogger

logger = getlogger()


class UTXOCache(OptimisticKVStore):
    """
    Used to answer 2 questions:
        1. Given​ ​an​ ​output,​ ​check​ ​if​ ​it's​ ​spent​ ​or​ ​not​ ​and​ ​return​ ​the​ ​amount​ ​
        held​ ​by​ ​it​ ​if​ ​not spent
        2. Given​ ​an​ ​address,​ ​return​ ​all​ ​valid​ ​UTXOs

    The key value looks like this `<key is address> -> <value is a list of unspent seq nos and amounts>`
    If address `a1` has 3 UTXOs with seq no 4, 6, 19 and amount 1, 31, 100 respectively,
    the key value would be `a1 -> 4:1:6:31:19:100`; for `n` seq_nos, there will be `2*n` items.
    The seq no lives at index `i` and value lives at `i+1`
    Intentionally not using tuples or any delimiter for seq_no, value pairs to avoid serialization and
    deserialization cost

    An unspent output is combination of an address and a reference (seq no)
    to a txn in which this address was transferred some tokens
    """
    def __init__(self, kv_store: KeyValueStorage):
        super().__init__(kv_store)

    @staticmethod
    def _is_valid_output(output: Output):
        if not isinstance(output, Output):
            raise UTXOError("Output is invalid object type")

    # Adds an output to the batch of uncommitted outputs
    def add_output(self, output: Output, is_committed=False):
        UTXOCache._is_valid_output(output)
        key = self._create_key(output)
        try:
            seq_nos_amounts = self.get(key, is_committed)
            seq_nos_amounts = self._parse_val(seq_nos_amounts)
        except KeyError:
            seq_nos_amounts = []
        logger.debug('adding new output: key {} seq_nos_amounts {} '
                     'output {}'.format(key, seq_nos_amounts, output))
        seq_nos_amounts.append(str(output.seq_no))
        seq_nos_amounts.append(str(output.value))
        val = self._create_val(seq_nos_amounts)
        self.set(key, val, is_committed=is_committed)

    # Spends the provided output by fetching it from the key value store
    # (it must have been previously added) and then doing batch ops
    def spend_output(self, output: Output, is_committed=False):
        UTXOCache._is_valid_output(output)

        key = self._create_key(output)

        try:  # Looking at OptimisticKVStore, there is not way to test if key is in store
            seq_nos_amounts = self.get(key, is_committed)
        except KeyError:
            raise UTXONotFound("seq_no for address were not found")

        logger.debug('spending output type2 key {} seq_nos_amounts {} output {}'.format(key, seq_nos_amounts, output))
        seq_nos_amounts = self._parse_val(seq_nos_amounts)
        seq_no_str = str(output.seq_no)

        self.remove_seq_no(seq_no_str, seq_nos_amounts)

        val = self._create_val(seq_nos_amounts)
        self.set(key, val, is_committed=is_committed)

    # Retrieves a list of the unspent outputs from the key value storage that
    # are associated with the provided address
    def get_unspent_outputs(self, address: str,
                            is_committed=False) -> List[Output]:
        try:  # Looking at OptimisticKVStore, there is not way to test if key is in store
            seq_nos_amounts = self.get(address, is_committed)
        except KeyError:
            return []
        return self._build_outputs_from_val(address, seq_nos_amounts)

    def sum_inputs(self, inputs: list, is_committed=False):
        addresses = defaultdict(set)
        for addr, seq_no in inputs:
            addresses[addr].add(seq_no)

        output_val = 0
        for addr, seq_nos in addresses.items():
            try:
                seq_nos_amounts = self.get(addr, is_committed)
            except KeyError:
                raise AddressNotFound('Address {} was not found'.format(addr))

            seq_nos_amounts = self._parse_val(seq_nos_amounts)
            total = self._sum_amounts_from_seq_nos_amounts(seq_nos, seq_nos_amounts)

            output_val += total

        return output_val

    @staticmethod
    def _create_key(output: Output) -> str:
        return '{}'.format(output.address)

    @staticmethod
    def _create_val(items: List) -> str:
        return ':'.join(items)

    @staticmethod
    def _parse_val(val: str) -> List:
        if isinstance(val, (bytes, bytearray)):
            val = val.decode()
        if not isinstance(val, str):
            raise UTXOError("Items are not valid string -- '{}'".format(str(val)))

        return [] if not val else val.split(':')

    @staticmethod
    def _build_outputs_from_val(address: str, val: str) -> List[Output]:
        items = UTXOCache._parse_val(val)
        if len(items) % 2 != 0:
            raise ValueError('Length of items should be even: items={}'.format(len(items)))

        return [Output(address, int(items[i]), int(items[i + 1]))
                for i in range(0, len(items), 2)]

    @staticmethod
    def remove_seq_no(seq_no_str: str, seq_nos_amounts: List[str]):
        # Shortens the passed list `seq_nos_amounts` by 2 items
        for i in range(0, len(seq_nos_amounts), 2):
            if seq_nos_amounts[i] == seq_no_str:
                break
        else:
            err_msg = "seq_no {} is not found is list of seq_nos_amounts for address -- current list: {}".format(
                seq_no_str,
                seq_nos_amounts)
            raise UTXONotFound(err_msg)

        seq_nos_amounts.pop(i)
        # List has changed length, value at index `i+1` has moved to index `i`
        seq_nos_amounts.pop(i)

    @staticmethod
    def _sum_amounts_from_seq_nos_amounts(required_seq_nos: Set[int], seq_nos_amounts: List[str]) -> int:
        total = 0
        for i in range(0, len(seq_nos_amounts), 2):
            if int(seq_nos_amounts[i]) in required_seq_nos:
                total += int(seq_nos_amounts[i + 1])
                required_seq_nos.remove(int(seq_nos_amounts[i]))
                if not required_seq_nos:
                    break

        if required_seq_nos:
            err_msg = "seq_nos {} are not found is list of seq_nos_amounts for address -- current list: {}".format(
                required_seq_nos,
                seq_nos_amounts)
            raise UTXONotFound(err_msg)

        return total
