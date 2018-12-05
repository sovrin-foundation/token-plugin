from heapq import heappush, heappop
from typing import List

from base58 import b58decode_check, b58encode_check, b58encode, b58decode
from plenum.common.exceptions import UnauthorizedClientRequest
from plenum.common.types import f
from plenum.common.roles import Roles
from plenum.server.domain_req_handler import DomainRequestHandler


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
        ordered = []
        while self._heap:
            ordered.append(heappop(self._heap))
        return ordered


def validate_multi_sig_txn(request, required_role, domain_state, threshold: int):
    # Takes a request, a provided role and expects to find at least a threshold number
    # senders roles with provided role. Can raise an exception
    senders = request.all_identifiers
    error = ''
    if len(senders) >= threshold:
        authorized_sender_count = 0
        for idr in senders:
            if DomainRequestHandler.get_role(domain_state, idr, required_role):
                authorized_sender_count += 1
                if authorized_sender_count == threshold:
                    return
        error = 'only {} can send this transaction'. \
            format(Roles(required_role).name)
    else:
        error = 'Request needs at least {} signers but only {} found'. \
            format(threshold, len(senders))

    if error:
        raise UnauthorizedClientRequest(senders, getattr(request, f.REQ_ID.nm, None), error)

