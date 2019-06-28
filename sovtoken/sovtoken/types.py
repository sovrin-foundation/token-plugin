from typing import NamedTuple, Set, Optional
import json


class Output:
    def __init__(self, address: str, seq_no: int, value: Optional[int]):
        self.address = address
        self.seqNo = seq_no
        self.amount = value

    def less_than(self, other):
        return self.seqNo < other.seqNo

    def __lt__(self, other):
        return self.less_than(other)

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, Output) \
               and self.address == other.address \
               and self.seqNo == other.seqNo \
               and self.amount == other.amount

    def __hash__(self) -> int:
        return hash(self.address) + hash(self.seqNo) + hash(self.amount)


OutputList = NamedTuple("OutputList",
                        [("spent", Set[int]), ("unspent", Set[int])])
