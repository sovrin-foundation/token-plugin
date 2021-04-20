from plenum.common.signer_simple import SimpleSigner

from sovtoken.util import verkey_to_address
from sovtoken.test.wallet import Address

VALID_IDENTIFIER = "6ouriXMZkLeHsuXrN1X1fd"
VALID_REQID = 1517423828260117
CONS_TIME = 1518541344
PROTOCOL_VERSION = 1
SIGNATURES = {'B8fV7naUqLATYocqu7yZ8W':
              '27BVCWvThxMV9pzqz3JepMLVKww7MmreweYjh15LkwvAH4qwYAMbZWeYr6E6LcQexYAikTHo212U1NKtG8Gr2PPP',
              'CA4bVFDU4GLbX8xZju811o':
                  '3A1Pmkox4SzYRavTj9toJtGBr1Jy9JvTTnHz5gkS5dGnY3PhDcsKpQCBfLhYbKqFvpZKaLPGT48LZKzUVY4u78Ki',
              'E7QRhdcnhAwA6E46k9EtZo':
                  'MsZsG2uQHFqMvAsQsx5dnQiqBjvxYS1QsVjqHkbvdS2jPdZQhJfackLQbxQ4RDNUrDBy8Na6yZcKbjK2feun7fg',
              'M9BJDuS24bqbJNvBRsoGg3':
                  '5BzS7J7uSuUePRzLdF5BL5LPvnXxzQyB5BqMT19Hz8QjEyb41Mum71TeNvPW9pKbhnDK12Pciqw9WRHUvsfwdYT5'}


VALID_ADDR_1 = Address(seed='se000000000000000000000000000000'.encode()).address
VALID_ADDR_2 = Address(seed='sf000000000000000000000000000000'.encode()).address


(VALID_ADDR_3, VALID_ADDR_4, VALID_ADDR_5, VALID_ADDR_6, VALID_ADDR_7) = \
    (verkey_to_address(SimpleSigner().verkey) for _ in range(5))
