from pymongo import MongoClient


__mongo_server = "mongodb://powerchain:powerchain@localhost:27017/"
__database_name = "powerchain"


def init_mongo():
    __client = MongoClient(__mongo_server)
    MongoConnection.db = __client[__database_name]


class MongoConnection:
    db = None

    def get_collection(collection_name):
        if MongoConnection.db == None:
            init_mongo()
        return MongoConnection.db[collection_name]
