from pymongo import MongoClient


__mongo_server = "mongodb://powerchain:powerchain@localhost:27017/"
__database_name = "powerchain"


class __MongoConnection:
    db = None


def init_mongo():
    __client = MongoClient(__mongo_server)
    __MongoConnection.db = __client[__database_name]


def get_collection(collection_name):
    if __MongoConnection.db == None:
        init_mongo()
    return __MongoConnection.db[collection_name]
