from base58 import b58decode

from plenum.common.signer_simple import SimpleSigner
from sovtoken.types import Output
from sovtoken.util import verkey_to_address, \
    address_to_verkey, SortedItems


def test_address_to_verkey_and_vice_versa():
    for _ in range(100):
        signer = SimpleSigner()
        assert len(signer.naclSigner.verraw) == 32
        address = verkey_to_address(signer.verkey)
        assert len(b58decode(address)) == 36
        verkey = address_to_verkey(address)
        assert len(b58decode(verkey)) == 32
        assert signer.naclSigner.verraw == b58decode(verkey)
        assert signer.verkey == verkey


def test_outputs_in_order():
    o1 = Output('a', 1, 8)
    o2 = Output('a', 2, 9)
    o3 = Output('a', 9, 10)
    o4 = Output('a', 22, 11)
    o5 = Output('b', 3, 3)
    o6 = Output('b', 6, 6)
    o7 = Output('b', 4, 7)

    sr = SortedItems()
    sr.add(o6)
    sr.add(o5)
    sr.add(o2)
    sr.add(o7)
    sr.add(o1)
    sr.add(o4)
    sr.add(o3)

    assert sr.sorted_list == [Output(address='a', seq_no=1, value=8), Output(address='a', seq_no=2, value=9),
                              Output(address='b', seq_no=3, value=3), Output(address='b', seq_no=4, value=7),
                              Output(address='b', seq_no=6, value=6), Output(address='a', seq_no=9, value=10),
                              Output(address='a', seq_no=22, value=11)]

    outputs = [Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=312, value=1),
               Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=313, value=1),
               Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=314, value=1),
               Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=315, value=1),
               Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=316, value=1),
               Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=319, value=1),
               Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=317, value=1),
               Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=321, value=1),
               Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=318, value=1)]

    si = SortedItems()
    for o in outputs:
        si.add(o)

    assert si.sorted_list == [Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=312, value=1),
                              Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=313, value=1),
                              Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=314, value=1),
                              Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=315, value=1),
                              Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=316, value=1),
                              Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=317, value=1),
                              Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=318, value=1),
                              Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=319, value=1),
                              Output(address='2w3WMmR92ijMH3ZV9qNoAUh1i7HjCyqVbBt7e771DdwEWL1K2W', seq_no=321, value=1)]
