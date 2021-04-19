from collections import defaultdict
from typing import List, Set

from sovtoken.exceptions import UTXONotFound, UTXOError, UTXOAddressNotFound
from sovtoken.types import Output
from storage.kv_store import KeyValueStorage
from storage.optimistic_kv_store import OptimisticKVStore
from stp_core.common.log import getlogger

logger = getlogger()


class UTXOCache(OptimisticKVStore):
    """
    Used to answer 2 questions:
        1. Given an output, check whether it is spent. Return the amout it holds when not spent.
        2. Given an address, return all valid UTXOs.

    The key value looks like this
        `<key is address> -> <value is a list of unspent seq nos and amounts>`

    If address `a1` has 3 UTXOs with seq no 4, 6, 19 and amount 1, 31, 100 respectively,
    the key value would be `a1 -> 4:1:6:31:19:100`
        * For `n` seq_nos, there will be `2*n` items in the value list
        * The seq no lives at index `i` and the corresponding value lives at `i+1`
        * Avoiding tuples or any additional delimiters for seq_no:value pairs to avoid serialization and
        deserialization cost

    An unspent output is the combination of an address and a reference (seq no) to a txn in which this address was
    transferred some tokens
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

        logger.debug('adding new output: output:{}'.format(str(output)))

        seq_nos_amounts = UTXOAmounts.get_amounts(output.address, self, make_new=True, is_committed=is_committed)

        seq_nos_amounts.add_amount(output.seqNo, output.amount)
        self.set(output.address, seq_nos_amounts.as_str(), is_committed=is_committed)

    # Spends the provided output by fetching it from the key value store
    # (it must have been previously added) and then doing batch ops
    def spend_output(self, output: Output, is_committed=False):
        UTXOCache._is_valid_output(output)

        logger.debug('spending output -- output:{}'.format(str(output)))

        seq_nos_amounts = UTXOAmounts.get_amounts(output.address, self, is_committed=is_committed)

        seq_nos_amounts.remove_seq_no(output.seqNo)

        self.set(output.address, seq_nos_amounts.as_str(), is_committed=is_committed)

    # Retrieves a list of the unspent outputs from the key value storage that
    # are associated with the provided address
    def get_unspent_outputs(self, address: str,
                            is_committed=False) -> List[Output]:
        seq_nos_amounts = UTXOAmounts.get_amounts(address, self, make_new=True, is_committed=is_committed)
        return seq_nos_amounts.as_output_list()

    def sum_inputs(self, inputs: list, is_committed=False):
        addresses = defaultdict(set)
        for inp in inputs:
            addr = inp["address"]
            seq_no = inp["seqNo"]
            addresses[addr].add(seq_no)

        output_val = 0
        for addr, seq_nos in addresses.items():
            seq_nos_amounts = UTXOAmounts.get_amounts(addr, self, is_committed=is_committed)

            total = seq_nos_amounts.sum_amounts(seq_nos)

            output_val += total

        return output_val

    def close(self):
        if self._store:
            self._store.close()

    @staticmethod
    def _create_key(output: Output) -> str:
        return '{}'.format(output.address)


class UTXOAmounts:
    DELIMITER = ':'

    @classmethod
    def get_amounts(cls, address: str, cache: UTXOCache, make_new=False, is_committed=False):
        key = address

        try:
            data = cache.get(key, is_committed=is_committed)
            return cls(key, data=data)
        except KeyError:
            if make_new:
                return cls(key, None)
            else:
                raise UTXOAddressNotFound('Address {} was not found'.format(key))

    def __init__(self, address: str, data=None):
        self.address = address

        if data:
            if isinstance(data, (bytes, bytearray)):
                data = data.decode()

            if not isinstance(data, str):
                raise UTXOError("Items are not valid string -- '{}'".format(str(data)))

            split = data.split(self.DELIMITER)

            if not len(split) % 2 == 0:  # test if even
                raise UTXOError("Stored seqNo-amount pairs is not even")
            self.data = split
        else:
            self.data = []

    def add_amount(self, seq_no: int, amount: int):
        if not isinstance(seq_no, int) or not isinstance(amount, int):
            raise UTXOError("Adding invalid types -- seqNo:{} amount:{}".format(seq_no, amount))

        logger.debug('adding seq_no: address {} - seq_no: {} - amount: {}'.format(self.address, seq_no, amount))

        self.data.append(str(seq_no))
        self.data.append(str(amount))

    def remove_seq_no(self, seq_no: int):
        logger.debug('removing seq_no -- address:{} - seq_no: {} - data: {}'.format(self.address,
                                                                                    seq_no,
                                                                                    str(self.data)))

        seq_no_str = str(seq_no)
        # Shortens the passed list `seq_nos_amounts` by 2 items
        for i in range(0, len(self.data), 2):
            if self.data[i] == seq_no_str:
                break
        else:
            err_msg = "seq_no {} is not found is list of seq_nos_amounts for address -- current list: {}".format(
                seq_no_str,
                self.data)
            raise UTXONotFound(err_msg)

        if i < len(self.data) and (i + 1) < len(self.data):
            self.data.pop(i)
            # List has changed length, value at index `i+1` has moved to index `i`
            self.data.pop(i)
        else:
            raise UTXOError("Unable to remove seq_no from address")

    def sum_amounts(self, seq_nos: Set[int]) -> int:
        total = 0
        for i in range(0, len(self.data), 2):
            if int(self.data[i]) in seq_nos:
                total += int(self.data[i + 1])
                seq_nos.remove(int(self.data[i]))
                if not seq_nos:
                    break

        if seq_nos:
            err_msg = "seq_nos {} are not found in list of seq_nos_amounts for address {} -- current list: {}".format(
                seq_nos,
                self.address,
                self.data)
            raise UTXONotFound(err_msg)

        return total

    def as_output_list(self) -> List[Output]:
        if len(self.data) % 2 != 0:
            raise UTXOError('Length of seqNo-amount pairs must be even: items={}'.format(len(self.data)))

        rtn = []
        for i in range(0, len(self.data), 2):
            try:
                seq_no = int(self.data[i])
                amount = int(self.data[i + 1])
            except ValueError:
                raise UTXOError(
                    "Invalid data -- not integers -- seq_no:{} amount:{}, address:{}"
                    .format(self.data[i], self.data[i + 1], self.address)
                )
            rtn.append(Output(self.address, seq_no, amount))

        return rtn

    def as_str(self) -> str:
        if len(self.data) % 2 != 0:
            raise UTXOError('Length of seqNo-amount pairs must be even: items={}'.format(len(self.data)))

        return ':'.join(self.data)

    @staticmethod
    def _create_key(output: Output) -> str:
        return '{}'.format(output.address)
