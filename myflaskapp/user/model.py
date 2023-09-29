import random
from bson import ObjectId
from passlib.hash import sha256_crypt
from geopy.geocoders import Nominatim

from util import ethereum_connection
from util.db_connection import get_database_connection


__user_collection_name = "user"
__user_collection = get_database_connection(__user_collection_name)

__ethereum_connection = ethereum_connection()


class User:
    def __init__(
        self, username, password, email, name, geo_coordinate, bcaddress
    ) -> None:
        self.username = username
        self.password = password
        self.email = email
        self.name = name
        self.geo_coordinate = geo_coordinate
        self.current_energy = random.randint(0, 800)
        self.energy_sold = 0
        self.energy_purchased = 0
        self.bcaddress = bcaddress

    def initialize_geo_address(self):
        geolocator = Nominatim(user_agent="myGeocoder")
        location = geolocator.reverse(self.geo_coordinate)
        self.geo_address = location.address if location else ""

    def save(self):
        if self.id is None:
            result = __user_collection.insert_one(self.toJson())
            self.id = result.inserted_id
        else:
            __user_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": self.toJson()},
            )

    def get_ethereum_balance():
        ganache_account = __ethereum_connection.eth.accounts[0]
        ethereum_balance_wei = __ethereum_connection.eth.get_balance(ganache_account)
        ethereum_balance = __ethereum_connection.from_wei(ethereum_balance_wei, "ether")
        return ethereum_balance

    def get_ethereum_used_balance():
        ganache_account = __ethereum_connection.eth.accounts[0]
        ethereum_used_balance_wei = __ethereum_connection.eth.get_transaction_count(
            ganache_account
        )
        ethereum_used_balance = __ethereum_connection.from_wei(
            ethereum_used_balance_wei, "ether"
        )
        return ethereum_used_balance

    def toJson(self):
        return {
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "name": self.name,
            "geo_coordinate": self.geo_coordinate,
            "geo_address": self.geo_address,
            "current_energy": self.current_energy,
            "energy_sold": self.energy_sold,
            "energy_purchased": self.energy_purchased,
            "bcaddress": self.bcaddress,
        }

    # static methods

    def __fromJson(json):
        return User(
            json["username"],
            json["password"],
            json["email"],
            json["name"],
            json["geo_coordinate"],
            json["geo_address"],
            json["current_energy"],
            json["energy_sold"],
            json["energy_purchased"],
            json["bcaddress"],
        )
    
    def __fromJsonArray(jsonArray):
        users = []
        for j in jsonArray:
            users.append(User.__fromJson(j))
        return users

    def is_email_registered(email) -> bool:
        result = __user_collection.find_one({"email": email})
        return result != None

    def get_login_user(username, password):
        result = __user_collection.find_one({"username": username})
        if result == None:
            raise Exception("Invalid username or password")

        user = User.__fromJson(result)
        verified = sha256_crypt.verify(password, user.password)
        if not verified:
            raise Exception("Invalid username or password")

        return user

    def get_by_username(username):
        result = __user_collection.find_one({"username": username})
        return User.__fromJson(result)

    def get_all():
        results = __user_collection.find()
        return User.__fromJsonArray(results)

    def get_other_users_with_available_energy(user_id):
        results = __user_collection.find(
            {"energy_balance": {"$gt": 0}, "_id": {"$ne": ObjectId(user_id)}}
        )
        return User.__fromJsonArray(results)

    def get_ethereum_account():
        return __ethereum_connection.eth.accounts
