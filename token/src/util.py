def register_token_wallet_with_client(client, token_wallet):
    client.registerObserver(token_wallet.on_reply_from_network)


def update_token_wallet_with_result(wallet, result):
    wallet.on_reply_from_network(None, None, None, result, None)
