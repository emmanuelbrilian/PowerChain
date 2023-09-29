from bson import ObjectId
from util.db_connection import get_database_connection


__notification_collection_name = "seller_notifications"
__notification_collection = get_database_connection(__notification_collection_name)


class Notification:
    def __init__(
        self, purchase_id, buyer_username, seller_id, seller_username, energy_requested
    ) -> None:
        self.purchase_id = purchase_id
        self.buyer_username = buyer_username
        self.seller_id = seller_id
        self.seller_username = seller_username
        self.energy_requested = energy_requested
        self.status = "PENDING"

    def save(self):
        if self.id is None:
            result = __notification_collection.insert_one(self.__toJson())
            self.id = result.inserted_id
        else:
            __notification_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": self.__toJson()},
            )

    def __toJson(self):
        return {
            "purchase_id": self.purchase_id,
            "buyer_username": self.buyer_username,
            "seller_id": self.seller_id,
            "seller_username": self.seller_username,
            "energy_taken": self.energy_requested,
            "status": self.status,
        }

    # static methods

    def __fromJson(json):
        return Notification(
            json["_id"],
            json["purchase_id"],
            json["buyer_username"],
            json["seller_id"],
            json["seller_username"],
            json["energy_taken"],
            json["status"],
        )

    def __fromJsonArray(jsonArray):
        notifications = []
        for j in jsonArray:
            notifications.append(Notification.__fromJson(j))
        return notifications

    def get_pending_notifications_by_seller(seller_id) -> list:
        results = __notification_collection.find(
            {"seller_id": seller_id, "status": "PENDING"}
        )
        return Notification.__fromJsonArray(results)

    def get_by_id(id):
        result = __notification_collection.find_one({"_id": ObjectId(id)})
        return Notification.__fromJson(result)
