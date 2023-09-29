from pymongo import MongoClient


__mongo_server = "mongodb://localhost:27017/"
__database_name = "peer_selection"

__client = MongoClient(__mongo_server)
__db = __client[__database_name]

def get_database_connection(collection):
  return __db[collection]
