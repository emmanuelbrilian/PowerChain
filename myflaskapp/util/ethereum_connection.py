from web3 import Web3

__ethereum_address = "http://localhost:8545"


def __connect_to_ganache():
    ethereum_provider = Web3.HTTPProvider(__ethereum_address)
    return Web3(ethereum_provider)


def init_ethereum():
    EthereumConnection.ethereum_connection = __connect_to_ganache()


class EthereumConnection:
    ethereum_connection = None

    def get_ethereum_connetion():
        if EthereumConnection == None:
            init_ethereum()
        return EthereumConnection.ethereum_connection
