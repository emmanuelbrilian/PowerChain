from bson import ObjectId
from util.db_connection import MongoConnection


class Notification:
    __notification_collection_name = "notifications"

    __notification_collection = MongoConnection.get_collection(__notification_collection_name)

    def __init__(
        self,
        purchase_id,
        buyer_username,
        seller_id,
        seller_username,
        requested_energy,
        status="PENDING",
        id=None,
    ) -> None:
        self.id = id
        self.purchase_id = purchase_id
        self.buyer_username = buyer_username
        self.seller_id = seller_id
        self.seller_username = seller_username
        self.requested_energy = requested_energy
        self.status = status

    def save(self):
        data = self.__to_json()
        del data["_id"]

        if self.id is None:
            result = Notification.__notification_collection.insert_one(data)
            self.id = result.inserted_id
        else:
            Notification.__notification_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": data},
            )

    def __to_json(self):
        return {
            "_id": self.id,
            "purchase_id": self.purchase_id,
            "buyer_username": self.buyer_username,
            "seller_id": self.seller_id,
            "seller_username": self.seller_username,
            "requested_energy": self.requested_energy,
            "status": self.status,
        }

    # static methods

    def __from_json(json):
        return Notification(
            id=str(json["_id"]),
            purchase_id=json["purchase_id"],
            buyer_username=json["buyer_username"],
            seller_id=json["seller_id"],
            seller_username=json["seller_username"],
            requested_energy=json["requested_energy"],
            status=json["status"],
        )

    def __from_json_array(jsonArray):
        notifications = []
        for j in jsonArray:
            notifications.append(Notification.__from_json(j))
        return notifications

    def get_pending_notifications_by_seller(seller_id) -> list:
        results = Notification.__notification_collection.find(
            {"seller_id": seller_id, "status": "PENDING"}
        )
        return Notification.__from_json_array(results)

    def get_by_id(id):
        result = Notification.__notification_collection.find_one({"_id": ObjectId(id)})
        if result == None:
            return None
        return Notification.__from_json(result)

    def get_pending_notification_by_purchase_and_seller(purchase_id, seller_id):
        result = Notification.__notification_collection.find_one(
            {"purchase_id": purchase_id, "seller_id": seller_id, "status": "PENDING"}
        )
        if result == None:
            return None
        return Notification.__from_json(result)

    def abort_purchase_order_notifications(purchase_id):
        Notification.__notification_collection.update_many(
            {"purchase_id": purchase_id, "status": "PENDING"},
            {"$set": {"status": "ABORTED"}},
        )
