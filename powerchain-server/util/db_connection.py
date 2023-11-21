import logging
from pymongo import MongoClient


__LOG = logging.getLogger("MongoConnection")

__database_name = "powerchain"

__mongo_connection = None

class MongoConnection:
    def __init__(self, mongo_host) -> None:
        self.db = None
        self.mongo_host = mongo_host
        self.mongo_port = 27017

    def get_mongo_url(self):
        return f"mongodb://powerchain:powerchain@{self.mongo_host}:{self.mongo_port}"


def init_mongo(mongo_host):
    global __mongo_connection
    if __mongo_connection == None:
        __mongo_connection = MongoConnection(mongo_host)
    __connect_mongo(__mongo_connection.get_mongo_url())


def __connect_mongo(mongo_url):
    global __mongo_connection
    __LOG.info(f"Connecting to mongo host at {mongo_url}")
    __client = MongoClient(mongo_url)
    __mongo_connection.db = __client[__database_name]


def get_collection(collection_name):
    global __mongo_connection
    if __mongo_connection.db == None:
        init_mongo(__mongo_connection.mongo_host)
    return __mongo_connection.db[collection_name]
