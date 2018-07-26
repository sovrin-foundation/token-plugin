class HelperWallet():
    """
    Helper for dealing with the wallet and addresses

    # Methods
    - add_new_addresses
    """

    def add_new_addresses(wallet, n):
        """ Create and add n new addresses to a wallet """
        addresses = []
        for _ in range(num):
            address = Address()
            wallet.add_new_address(address=address)
            addresses.append(address)

        return addresses
