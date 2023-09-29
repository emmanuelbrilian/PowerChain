import logging

from bson import ObjectId
from geopy.distance import geodesic

from util.db_connection import get_database_connection


class PurchaseOrder:
    __LOG = logging.getLogger("PurchaseOrderModel")

    __purchase_order_collection_name = "purchase_orders"

    __purchase_order_collection = get_database_connection(
        __purchase_order_collection_name
    )

    def __init__(
        self,
        requested_amount,
        buyer_id,
        buyer_username,
        buyer_coordinate,
        provider_type=None,
        candidates=[],
        status="ON_GOING",
        id=None,
    ) -> None:
        self.id = id
        self.buyer_id = buyer_id
        self.buyer_username = buyer_username
        self.buyer_coordinate = buyer_coordinate
        self.requested_amount = requested_amount
        self.provider_type = provider_type
        self.candidates = candidates
        self.status = status

    def __calculate_distance(self, coord1, coord2):
        lat1, lon1 = map(float, coord1.split(", "))
        lat2, lon2 = map(float, coord2.split(", "))
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers

    def sortCandidatesByDistance(self, peers):
        candidates = []
        for seller in peers:
            energy_balance = int(seller.current_energy)
            distance = self.__calculate_distance(
                self.buyer_coordinate, seller.geo_coordinate
            )

            candidates.append(
                Candidate(seller.id, seller.username, distance, energy_balance)
            )

        PurchaseOrder.__LOG.debug(f"Found {len(candidates)} candidates")
        candidates.sort(key=lambda c: c.distance)
        self.candidates = candidates

    def isTotalEnergySufficient(self) -> bool:
        available_energies = map(lambda c: c.available_energy, self.candidates)
        total_available_energy = sum(available_energies)
        PurchaseOrder.__LOG.debug(
            f"Total available energy: {total_available_energy}, requested energy: {self.requested_amount}"
        )
        return total_available_energy < self.requested_amount

    def decideProviderType(self):
        first_candidate_energy = self.candidates[0].available_energy
        self.provider_type = (
            "SINGLE" if first_candidate_energy >= self.requested_amount else "MULTIPLE"
        )

    def select_single_provider_candidate(self):
        candidate = self.candidates[0]
        candidate.energy_requested = self.requested_amount
        candidate.status = "PENDING"
        return candidate

    def select_multiple_provider_candidates(self):
        selected_candidates = []
        total_energy = 0
        for candidate in self.candidates:
            if total_energy >= self.requested_amount:
                break

            energy_needs = self.requested_amount - total_energy
            energy_balance = candidate.available_energy
            energy_requested = min(energy_needs, energy_balance)

            candidate.energy_requested = energy_requested
            candidate.status = "PENDING"

            selected_candidates.append(candidate)
            total_energy += energy_requested

        return selected_candidates

    def save(self):
        data = self.__toJson()
        del data["_id"]

        if self.id is None:
            result = PurchaseOrder.__purchase_order_collection.insert_one(data)
            self.id = result.inserted_id
        else:
            PurchaseOrder.__purchase_order_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": data},
            )

    def __toJson(self):
        return {
            "_id": self.id,
            "buyer_id": self.buyer_id,
            "buyer_username": self.buyer_username,
            "buyer_coordinates": self.buyer_coordinate,
            "requested_amount": self.requested_amount,
            "provider_type": self.provider_type,
            "status": self.status,
            "candidate": Candidate.toJsonArray(self.candidates),
        }

    # class methods

    def fromJson(json):
        return PurchaseOrder(
            id=str(json["_id"]),
            buyer_id=json["buyer_id"],
            buyer_username=json["buyer_username"],
            buyer_coordinates=json["buyer_coordinates"],
            requested_amount=json["requested_amount"],
            provider_type=json["provider_type"],
            status=json["status"],
            candidates=Candidate.fromJsonArray(json["candidate"]),
        )

    def getById(id):
        result = PurchaseOrder.__purchase_order_collection.find_one(
            {"_id": ObjectId(id)}
        )
        return PurchaseOrder(result)

    def __update_candidate_on_response(purchase_id, seller_id, status):
        PurchaseOrder.__purchase_order_collection.update_one(
            {"_id": ObjectId(purchase_id), "candidate.user_id": seller_id},
            {"$set": {"candidate.$.status": status}},
        )

    def update_candidate_decline_request(purchase_id, seller_id):
        PurchaseOrder.__update_candidate_on_response(purchase_id, seller_id, "DECLINED")

    def update_candidate_approve_request(purchase_id, seller_id):
        PurchaseOrder.__update_candidate_on_response(purchase_id, seller_id, "APPROVED")


class Candidate:
    def __init__(
        self,
        seller_id,
        seller_username,
        distance,
        available_energy,
        energy_requested=0,
        status=None,
    ) -> None:
        self.seller_id = seller_id
        self.seller_username = seller_username
        self.distance = distance
        self.available_energy = available_energy
        self.energy_requested = energy_requested
        self.status = status

    def toJson(self):
        return {
            "seller_id": self.seller_id,
            "seller_username": self.seller_username,
            "distance": self.distance,
            "availabel_energy": self.available_energy,
            "energy_requested": self.energy_requested,
            "status": self.status,
        }

    def __fromJson(json) -> None:
        return Candidate(
            seller_id=json["seller_id"],
            seller_username=json["seller_username"],
            distance=json["distance"],
            available_energy=json["available_energy"],
            energy_requested=json["energy_requested"],
            status=json["status"],
        )

    def toJsonArray(candidates):
        json = []
        for c in candidates:
            json.append(c.toJson())
        return json

    def fromJsonArray(json):
        candidates = []
        for j in json:
            candidates.append(Candidate.__fromJson)
        return candidates
