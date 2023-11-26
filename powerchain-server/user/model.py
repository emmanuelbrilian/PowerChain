import logging

from bson import ObjectId
from passlib.hash import sha256_crypt
from geopy.geocoders import Nominatim

from util.ethereum_connection import get_ethereum_connetion
from util.db_connection import get_collection

class User:
    def __init__(
        self,
        username,
        password,
        email,
        name,
        geo_coordinates,
        bcaddress,
        current_energy,
        energy_sold=0,
        energy_purchased=0,
        geo_address=None,
        id=None,
    ) -> None:
        self.id = id
        self.username = username
        self.password = password
        self.email = email
        self.name = name
        self.geo_coordinates = geo_coordinates
        self.geo_address = geo_address
        self.current_energy = current_energy
        self.energy_sold = energy_sold
        self.energy_purchased = energy_purchased
        self.bcaddress = bcaddress

    def to_json(self):
        return {
            "_id": self.id,
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "name": self.name,
            "geo_coordinates": self.geo_coordinates,
            "geo_address": self.geo_address,
            "current_energy": self.current_energy,
            "energy_sold": self.energy_sold,
            "energy_purchased": self.energy_purchased,
            "bcaddress": self.bcaddress,
        }


__LOG = logging.getLogger("UserModel")

__USER_COLLECTION_NAME = "users"

def __get_collection():
    return get_collection(__USER_COLLECTION_NAME)


def from_json(json):
    return User(
        id=str(json["_id"]),
        username=json["username"],
        password=json["password"],
        email=json["email"],
        name=json["name"],
        geo_coordinates=json["geo_coordinates"],
        geo_address=json["geo_address"],
        current_energy=json["current_energy"],
        energy_sold=json["energy_sold"],
        energy_purchased=json["energy_purchased"],
        bcaddress=json["bcaddress"],
    )


def __from_json_array(jsonArray):
    users = []
    for j in jsonArray:
        users.append(from_json(j))
    return users


def initialize_geo_address(user: User):
    geolocator = Nominatim(user_agent="myGeocoder")
    location = geolocator.reverse(user.geo_coordinates)
    user.geo_address = location.address if location else ""


def save(user: User):
    collection = __get_collection()
    data = user.to_json()
    del data["_id"]

    if user.id is None:
        result = collection.insert_one(data)
        user.id = result.inserted_id
    else:
        collection.update_one(
            {"_id": ObjectId(user.id)},
            {"$set": data},
        )


def get_ethereum_balance(ganache_account):
    ethereum_connection = get_ethereum_connetion()
    ethereum_balance_wei = ethereum_connection.eth.get_balance(ganache_account)
    ethereum_balance = ethereum_connection.from_wei(ethereum_balance_wei, "ether")
    return ethereum_balance


def get_ethereum_used_balance(ganache_account):
    ethereum_connection = get_ethereum_connetion()
    ethereum_used_balance_wei = ethereum_connection.eth.get_transaction_count(
        ganache_account
    )
    ethereum_used_balance = ethereum_connection.from_wei(
        ethereum_used_balance_wei, "ether"
    )
    return ethereum_used_balance


def is_email_registered(email) -> bool:
    result = __get_collection().find_one({"email": email})
    return result != None


def get_login_user(username, password):
    result = __get_collection().find_one({"username": username})
    if result == None:
        __LOG.debug("Username ${username} is not found")
        raise Exception("Invalid username or password")

    user = from_json(result)
    verified = sha256_crypt.verify(password, user.password)
    if not verified:
        __LOG.debug("Password ${password} is incorrect")
        raise Exception("Invalid username or password")

    return user


def get_by_username(username):
    result = __get_collection().find_one({"username": username})
    return from_json(result)


def get_all():
    results = __get_collection().find()
    return __from_json_array(results)


def get_other_users_with_available_energy(user_id):
    results = __get_collection().find(
        {"current_energy": {"$gt": 0}, "_id": {"$ne": ObjectId(user_id)}}
    )
    return __from_json_array(results)


def __is_bcaddress_used(ethereum_account):
    result = __get_collection().find_one({"bcaddress": ethereum_account})
    return result != None


def get_ethereum_account():
    for ethereum_account in get_ethereum_connetion().eth.accounts:
        __LOG.debug(f"Found account: {ethereum_account}")
        if not __is_bcaddress_used(ethereum_account):
            return ethereum_account
    return None
