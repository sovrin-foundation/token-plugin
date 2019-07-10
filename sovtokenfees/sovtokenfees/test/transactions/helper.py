from collections import deque


def get_last_token_txn(nodeSet):
    return deque(nodeSet[0].ledgers[-1].getAllTxn()).pop()
