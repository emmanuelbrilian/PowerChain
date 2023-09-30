import random
import logging

from bson import ObjectId
from passlib.hash import sha256_crypt
from geopy.geocoders import Nominatim

from util.ethereum_connection import EthereumConnection
from util.db_connection import get_database_connection


class User:
    __USER_COLLECTION_NAME = "users"

    __LOG = logging.getLogger("UserModel")

    __user_collection = get_database_connection(__USER_COLLECTION_NAME)

    __ethereum_connection = EthereumConnection.get_ethereum_connetion()

    def __init__(
        self,
        username,
        password,
        email,
        name,
        geo_coordinates,
        bcaddress,
        current_energy=random.randint(0, 800),
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

    def initialize_geo_address(self):
        geolocator = Nominatim(user_agent="myGeocoder")
        location = geolocator.reverse(self.geo_coordinates)
        self.geo_address = location.address if location else ""

    def save(self):
        data = self.to_json()
        del data["_id"]

        if self.id is None:
            result = User.__user_collection.insert_one(data)
            self.id = result.inserted_id
        else:
            User.__user_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": data},
            )

    def get_ethereum_balance(self):
        ganache_account = User.__ethereum_connection.eth.accounts[0]
        ethereum_balance_wei = User.__ethereum_connection.eth.get_balance(
            ganache_account
        )
        ethereum_balance = User.__ethereum_connection.from_wei(
            ethereum_balance_wei, "ether"
        )
        return ethereum_balance

    def get_ethereum_used_balance(self):
        ganache_account = User.__ethereum_connection.eth.accounts[0]
        ethereum_used_balance_wei = (
            User.__ethereum_connection.eth.get_transaction_count(ganache_account)
        )
        ethereum_used_balance = User.__ethereum_connection.from_wei(
            ethereum_used_balance_wei, "ether"
        )
        return ethereum_used_balance

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

    # static methods

    def __from_json_array(jsonArray):
        users = []
        for j in jsonArray:
            users.append(User.from_json(j))
        return users

    def is_email_registered(email) -> bool:
        result = User.__user_collection.find_one({"email": email})
        return result != None

    def get_login_user(username, password):
        result = User.__user_collection.find_one({"username": username})
        if result == None:
            User.__LOG.debug("Username ${username} is not found")
            raise Exception("Invalid username or password")

        user = User.from_json(result)
        verified = sha256_crypt.verify(password, user.password)
        if not verified:
            User.__LOG.debug("Password ${password} is incorrect")
            raise Exception("Invalid username or password")

        return user

    def get_by_username(username):
        result = User.__user_collection.find({"username": username})
        return User.from_json(result)

    def get_all():
        results = User.__user_collection.find()
        return User.__from_json_array(results)

    def get_other_users_with_available_energy(user_id):
        User.__LOG.debug(f"Finding customer with balance other than {user_id}")
        results = User.__user_collection.find(
            {"current_energy": {"$gt": 0}, "_id": {"$ne": ObjectId(user_id)}}
        )
        return User.__from_json_array(results)

    def get_ethereum_account():
        return User.__ethereum_connection.eth.accounts
