from web3 import Web3

__ethereum_address = "http://localhost:8545"


class __EthereumConnection:
    ethereum_connection = None


def __connect_to_ganache():
    ethereum_provider = Web3.HTTPProvider(__ethereum_address)
    return Web3(ethereum_provider)


def init_ethereum():
    __EthereumConnection.ethereum_connection = __connect_to_ganache()


def get_ethereum_connetion():
    if __EthereumConnection.ethereum_connection == None:
        init_ethereum()
    return __EthereumConnection.ethereum_connection
