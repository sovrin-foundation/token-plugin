from base58 import b58decode_check, b58encode_check, b58encode, b58decode


def register_token_wallet_with_client(client, token_wallet):
    client.registerObserver(token_wallet.on_reply_from_network)


def update_token_wallet_with_result(wallet, result):
    wallet.on_reply_from_network(None, None, None, result, None)


def address_to_verkey(address):
    if isinstance(address, str):
        address = address.encode()
    try:
        vk_bytes = b58decode_check(address)
    except ValueError:
        raise ValueError('{} is not a valid base58check value'.format(address))
    return b58encode(vk_bytes)


def verkey_to_address(verkey):
    if isinstance(verkey, str):
        verkey = verkey.encode()
    return b58encode_check(b58decode(verkey))
