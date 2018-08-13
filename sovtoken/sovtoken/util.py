from heapq import heappush
from typing import List

from base58 import b58decode_check, b58encode_check, b58encode, b58decode

def register_token_wallet_with_client(client, token_wallet):
    client.registerObserver(token_wallet.on_reply_from_network)


def update_token_wallet_with_result(wallet, result):
    wallet.on_reply_from_network(None, None, None, result, None)


def address_to_verkey(address):
    vk_bytes = decode_address_to_vk_bytes(address)
    return b58encode(vk_bytes).decode()


def verkey_to_address(verkey):
    if isinstance(verkey, str):
        verkey = verkey.encode()
    return b58encode_check(b58decode(verkey)).decode()


def decode_address_to_vk_bytes(address):
    from plenum.common.exceptions import UnknownIdentifier

    if isinstance(address, str):
        address = address.encode()
    try:
        return b58decode_check(address)
    except ValueError:
        raise UnknownIdentifier('{} is not a valid base58check value'.format(address))


class SortedItems:
    # Used to keep the inserted items in sorted order.
    def __init__(self):
        self._heap = []

    def add(self, item):
        heappush(self._heap, item)

    @property
    def sorted_list(self) -> List:
        return list(self._heap)
