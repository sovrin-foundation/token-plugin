from base58 import b58decode

from plenum.common.signer_simple import SimpleSigner
from plenum.server.plugin.sovtoken.src.util import verkey_to_address, \
    address_to_verkey


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
