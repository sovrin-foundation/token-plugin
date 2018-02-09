from typing import List

from plenum.common.util import updateNamedTuple
from storage.kv_store import KeyValueStorage
from storage.optimistic_kv_store import OptimisticKVStore

from tokens.src.token_types import Output


class UTXOCache(OptimisticKVStore):
    # TODO: Extract storing in-memory`level`s like functionality from IdrCache
    """
    Used to answer 2 questions:
        1. Given​ ​an​ ​output,​ ​check​ ​if​ ​it's​ ​spent​ ​or​ ​not​ ​and​ ​return​ ​the​ ​amount​ ​
        held​ ​by​ ​it​ ​if​ ​not spent
        2. Given​ ​an​ ​address,​ ​return​ ​all​ ​valid​ ​UTXOs

    Stores 2 kinds of keys.
        Type1 key is an output prepended with "0"
        Type2 key is an address prepended with "1"
    """
    def __init__(self, kv_store: KeyValueStorage):
        super().__init__(kv_store)

    def add_output(self, output: Output, is_committed=False):
        type1_key = self._create_type1_key(output)
        type2_key = self._create_type2_key(output.address)
        type1_val = str(output.value)
        try:
            seq_nos = self.get(type2_key, is_committed)
            if isinstance(seq_nos, (bytes, bytearray)):
                seq_nos = seq_nos.decode()
            seq_nos = self._parse_type2_val(seq_nos)
        except KeyError:
            seq_nos = []
        seq_no_str = str(output.seq_no)
        if seq_no_str not in seq_nos:
            seq_nos.append(seq_no_str)
        type2_val = self._create_type2_val(seq_nos)
        batch = [(type1_key, type1_val), (type2_key, type2_val)]
        self.setBatch(batch, is_committed=is_committed)

    def get_output(self, output: Output, is_committed=False) -> Output:
        type1_key = self._create_type1_key(output)
        val = self.get(type1_key, is_committed)
        if not val:
            raise KeyError(type1_key)
        return Output(output.address, output.seq_no, int(val))

    def spend_output(self, output: Output, is_committed=False):
        type1_key = self._create_type1_key(output)
        type2_key = self._create_type2_key(output.address)
        seq_nos = self.get(type2_key, is_committed)
        if isinstance(seq_nos, (bytes, bytearray)):
            seq_nos = seq_nos.decode()
        seq_nos = self._parse_type2_val(seq_nos)
        seq_no_str = str(output.seq_no)
        if seq_no_str not in seq_nos:
            raise KeyError('{} not in {}'.format(seq_no_str, seq_nos))
        seq_nos.remove(seq_no_str)
        batch = [(self._store.WRITE_OP, type1_key, '')]
        # if seq_nos:
        type2_val = self._create_type2_val(seq_nos)
        batch.append((self._store.WRITE_OP, type2_key, type2_val))
        # else:
        #     batch.append((self._store.REMOVE_OP, type2_key, None))
        self.do_ops_in_batch(batch, is_committed=is_committed)

    def get_unspent_outputs(self, address: str,
                            is_committed=False) -> List[Output]:
        type2_key = self._create_type2_key(address)
        try:
            seq_nos = self.get(type2_key, is_committed)
            if isinstance(seq_nos, (bytes, bytearray)):
                seq_nos = seq_nos.decode()
            seq_nos = self._parse_type2_val(seq_nos)
        except KeyError:
            return []
        if not seq_nos:
            return []
        outputs = [Output(address, int(seq_no), None) for seq_no in seq_nos]
        return [updateNamedTuple(out, value=int(self.get(
            self._create_type1_key(out), is_committed))) for out in outputs]

    @staticmethod
    def _create_type1_key(output: Output) -> str:
        return '0:{}:{}'.format(output.address, output.seq_no)

    @staticmethod
    def _create_type2_key(address: str) -> str:
        return '1:{}'.format(address)

    @staticmethod
    def _create_type2_val(seq_nos: List) -> str:
        return ':'.join(seq_nos)

    @staticmethod
    def _parse_type2_val(seq_nos: str) -> List:
        return [] if not seq_nos else seq_nos.split(':')
