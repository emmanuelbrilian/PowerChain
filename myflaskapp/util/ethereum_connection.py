from web3 import Web3


class EthereumConnection:
    __ethereum_address = "http://localhost:7545"

    __ethereum_connection = None

    __mock = False

    def __connect_to_ganache(ganache_address):
        ethereum_provider = Web3.HTTPProvider(ganache_address)
        return Web3(ethereum_provider)

    def get_ethereum_connetion():
        if EthereumConnection.__mock:
            return GanacheMock()

        if EthereumConnection.__ethereum_connection is None:
            EthereumConnection.__ethereum_connection = (
                EthereumConnection.__connect_to_ganache(
                    EthereumConnection.__ethereum_address
                )
            )
        return EthereumConnection.__ethereum_connection


# ganache mock
class GanacheMock:
    def __init__(self) -> None:
        self.eth = ETHMock()

    def from_wei(self, wei, str):
        if wei.type == "balance":
            return 100
        elif wei.type == "transaction_count":
            return 10
        else:
            return 0


class ETHMock:
    def __init__(self) -> None:
        self.accounts = [{"id": "123"}]

    def get_balance(self, ganache_account):
        return WeiMock("balance")

    def get_transaction_count(self, ganache_account):
        return WeiMock("transaction_count")


class WeiMock:
    def __init__(self, type) -> None:
        self.type = type
