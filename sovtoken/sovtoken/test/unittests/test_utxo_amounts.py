import pytest

from sovtoken.exceptions import UTXOError, UTXONotFound
from sovtoken.types import Output
from sovtoken.utxo_cache import UTXOAmounts


class MockUtxoCache:
    def __init__(self, data):
        self.data = data

    def get(self, key, is_committed=False):
        self.data.get(key)


VALID_ADDR_1 = '6baBEYA94sAphWBA5efEsaA6X2wCdyaH7PXuBtv2H5S1'


def test_get_amounts():
    mock = MockUtxoCache({VALID_ADDR_1: "1:300"})
    amounts = UTXOAmounts.get_amounts(VALID_ADDR_1, mock)
    assert amounts.address == VALID_ADDR_1
    assert isinstance(amounts.data, list)


def test_init():
    amount = UTXOAmounts(VALID_ADDR_1, "1:100")
    assert amount.address == VALID_ADDR_1
    assert len(amount.data) == 2
    assert amount.data[0] == "1"
    assert amount.data[1] == "100"

    with pytest.raises(UTXOError):
        UTXOAmounts(VALID_ADDR_1, "1:100:2")

    amount = UTXOAmounts(VALID_ADDR_1, None)
    assert len(amount.data) == 0


def test_init_more_complex():
    val = '10:11:12:5:13:6'
    amount = UTXOAmounts(VALID_ADDR_1, val)
    assert amount.data == ['10', '11', '12', '5', '13', '6']


def test_init_bytearray():
    val = bytearray(b'10:10')
    amount = UTXOAmounts(VALID_ADDR_1, val)
    assert amount.data == ['10', '10']

def test_init_invalid():
    val = [10, 11, 12, 5, 13, 6]
    with pytest.raises(UTXOError):
        UTXOAmounts(VALID_ADDR_1, val)


def test_parse_val_invalid_wrong_split():
    val = '10,11,12,5,13,6'

    with pytest.raises(UTXOError):
        UTXOAmounts(VALID_ADDR_1, val)

def test_parse_val_empty():
    amount = UTXOAmounts(VALID_ADDR_1, "")
    assert amount.data == []


def test_add_amount():
    amount = UTXOAmounts(VALID_ADDR_1, "1:100")
    amount.add_amount(3, 23)
    assert len(amount.data) == 4
    assert amount.data[2] == "3"
    assert amount.data[3] == "23"
    assert amount.as_str() == "1:100:3:23"

    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    amount.add_amount(3, 23)
    assert len(amount.data) == 6
    assert amount.data[4] == "3"
    assert amount.data[5] == "23"
    assert amount.as_str() == "1:100:2:332:3:23"

    with pytest.raises(UTXOError):
        amount = UTXOAmounts(VALID_ADDR_1, "1:100")
        amount.add_amount(None, 32)
        amount.add_amount(32, None)


def test_remove_seq_no():
    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    amount.remove_seq_no(2)
    assert len(amount.data) == 2

    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    with pytest.raises(UTXOError):
        amount.remove_seq_no(534)

    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    amount.data = ["1", "100", "2"]
    with pytest.raises(UTXOError):
        amount.remove_seq_no(2)


def test_as_output_list():
    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    output_list = amount.as_output_list()
    assert len(output_list) == 2
    for o in output_list:
        assert isinstance(o, Output)

    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    amount.data = ["1", "100", "2"]
    with pytest.raises(UTXOError):
        amount.as_output_list()


def test_as_str():
    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    str_val = amount.as_str()
    assert str_val == "1:100:2:332"

    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    amount.data = ["1", "100", "2"]
    with pytest.raises(UTXOError):
        amount.as_str()


def test_as_str_invalid():
    amount = UTXOAmounts(VALID_ADDR_1, "1:100:2:332")
    amount.data = [10, 11, 12, 5, 13, 6]
    with pytest.raises(TypeError):
        amount.as_str()

    amount.data = ['10', '11', '12', '5', '13', '6']
    val = amount.as_str()
    assert val == '10:11:12:5:13:6'


def test_as_output_list():
    with pytest.raises(UTXOError):
        UTXOAmounts(VALID_ADDR_1, '2:20:3:30:30:40:40:30:20').as_output_list()
    with pytest.raises(UTXOError):
        UTXOAmounts(VALID_ADDR_1, '2:20:3:30:30:40:40:30:20:').as_output_list()
    with pytest.raises(UTXOError):
        UTXOAmounts(VALID_ADDR_1, ':20:3:30:30:40:40:30:20:1').as_output_list()
    with pytest.raises(UTXOError):
        UTXOAmounts(VALID_ADDR_1, '20:3:30:30:40:40:30:20:1').as_output_list()
    with pytest.raises(UTXOError):
        UTXOAmounts(VALID_ADDR_1, '2:20:3:30::40:40:30:20:1').as_output_list()
    val = '2:20:3:30:30:40:40:30:20:1'
    assert UTXOAmounts(VALID_ADDR_1, val).as_output_list() == [Output(VALID_ADDR_1, 2, 20),
                                                               Output(VALID_ADDR_1, 3, 30),
                                                               Output(VALID_ADDR_1, 30, 40),
                                                               Output(VALID_ADDR_1, 40, 30),
                                                               Output(VALID_ADDR_1, 20, 1),
                                                               ]


def test_remove_seq_no():
    seq_nos_amounts = ":".join(['2', '20', '3', '30', '30', '40', '40', '30', '20', '1'])
    amounts = UTXOAmounts(VALID_ADDR_1, seq_nos_amounts)
    original_length = len(amounts.data)

    with pytest.raises(UTXONotFound):
        amounts.remove_seq_no(35)
        # UTXOCache.remove_seq_no('35', seq_nos_amounts)
    assert original_length == len(amounts.data)
    assert amounts.data == ['2', '20', '3', '30', '30', '40', '40', '30', '20', '1']

    amounts.remove_seq_no('2')
    assert original_length == len(amounts.data) + 2
    assert amounts.data == ['3', '30', '30', '40', '40', '30', '20', '1']

    amounts.remove_seq_no('40',)
    assert original_length == len(amounts.data) + 4
    assert amounts.data == ['3', '30', '30', '40', '20', '1']

    amounts.remove_seq_no('20')
    assert original_length == len(amounts.data) + 6
    assert amounts.data == ['3', '30', '30', '40']

    with pytest.raises(UTXONotFound):
        amounts.remove_seq_no('19')
    assert original_length == len(amounts.data) + 6
    assert amounts.data == ['3', '30', '30', '40']

    with pytest.raises(UTXONotFound):
        amounts.remove_seq_no('40')
    assert original_length == len(amounts.data) + 6
    assert amounts.data == ['3', '30', '30', '40']

    amounts.remove_seq_no('30')
    assert original_length == len(amounts.data) + 8
    assert amounts.data == ['3', '30']

    amounts.remove_seq_no('3')
    assert original_length == len(amounts.data) + 10
    assert amounts.data == []


def test_sum_amounts_from_seq_nos_amounts():
    seq_nos_amounts = ":".join(['2', '20', '3', '30', '30', '40', '40', '30', '20', '1'])
    amounts = UTXOAmounts(VALID_ADDR_1, seq_nos_amounts)

    with pytest.raises(UTXONotFound):
        amounts.sum_amounts({9})
    with pytest.raises(UTXONotFound):
        amounts.sum_amounts({2, 9})
    assert amounts.sum_amounts(set()) == 0
    assert amounts.sum_amounts({2}) == 20
    assert amounts.sum_amounts({2, 3}) == 50
    assert amounts.sum_amounts({30, 40}) == 70
    assert amounts.sum_amounts({20}) == 1
    assert amounts.sum_amounts({2, 30, 40, 3, 20}) == 121
