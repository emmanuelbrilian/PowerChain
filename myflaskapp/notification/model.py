from bson import ObjectId
from util.db_connection import get_database_connection


class Notification:
    __notification_collection_name = "notifications"

    __notification_collection = get_database_connection(__notification_collection_name)

    def __init__(
        self,
        purchase_id,
        buyer_username,
        seller_id,
        seller_username,
        energy_requested,
        status="PENDING",
        id=None,
    ) -> None:
        self.id = id
        self.purchase_id = purchase_id
        self.buyer_username = buyer_username
        self.seller_id = seller_id
        self.seller_username = seller_username
        self.energy_requested = energy_requested
        self.status = status

    def save(self):
        data = self.__toJson()
        del data["_id"]

        if self.id is None:
            result = Notification.__notification_collection.insert_one(data)
            self.id = result.inserted_id
        else:
            Notification.__notification_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": data},
            )

    def __toJson(self):
        return {
            "_id": self.id,
            "purchase_id": self.purchase_id,
            "buyer_username": self.buyer_username,
            "seller_id": self.seller_id,
            "seller_username": self.seller_username,
            "energy_requested": self.energy_requested,
            "status": self.status,
        }

    # static methods

    def __fromJson(json):
        return Notification(
            id=str(json["_id"]),
            purchase_id=json["purchase_id"],
            buyer_username=json["buyer_username"],
            seller_id=json["seller_id"],
            seller_username=json["seller_username"],
            energy_requested=json["energy_requested"],
            status=json["status"],
        )

    def __fromJsonArray(jsonArray):
        notifications = []
        for j in jsonArray:
            notifications.append(Notification.__fromJson(j))
        return notifications

    def get_pending_notifications_by_seller(seller_id) -> list:
        results = Notification.__notification_collection.find(
            {"seller_id": seller_id, "status": "PENDING"}
        )
        return Notification.__fromJsonArray(results)

    def get_by_id(id):
        result = Notification.__notification_collection.find_one({"_id": ObjectId(id)})
        return Notification.__fromJson(result)
