from web3 import Web3

__ethereum_address = "http://localhost:7545"
__ethereum_provider = Web3.HTTPProvider(__ethereum_address)
__ethereum_connection = Web3(__ethereum_provider)

def get_ethereum_connetion():
  return __ethereum_connection