from pymongo import MongoClient


__mongo_server = "mongodb://transactionhistory:transactionhistory@localhost:27017/"
__database_name = "powerchain"

__client = MongoClient(__mongo_server)
__db = __client[__database_name]

def get_database_connection(collection):
  return __db[collection]
