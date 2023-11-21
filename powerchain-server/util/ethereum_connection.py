import logging
from web3 import Web3

__LOG = logging.getLogger("EthereumCOnnection")


class __EthereumConnection:
    ethereum_connection = None
    ethereum_host = None
    ethereum_port = 8545

def __get_ethereum_url():
    return f"http://{__EthereumConnection.ethereum_host}:{__EthereumConnection.ethereum_port}"


def __connect_to_ganache(ethereum_address):
    __LOG.info(f"Conneting to ethereum host at {ethereum_address}")
    ethereum_provider = Web3.HTTPProvider(ethereum_address)
    return Web3(ethereum_provider)


def init_ethereum(ethereum_host):
    __EthereumConnection.ethereum_host = ethereum_host
    __EthereumConnection.ethereum_connection = __connect_to_ganache(__get_ethereum_url())


def get_ethereum_connetion():
    if __EthereumConnection.ethereum_connection == None:
        init_ethereum(__EthereumConnection.ethereum_host)
    return __EthereumConnection.ethereum_connection
