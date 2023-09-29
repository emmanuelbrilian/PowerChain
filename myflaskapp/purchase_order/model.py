from bson import ObjectId
from geopy.distance import geodesic

from util.db_connection import get_database_connection


__purchase_order_collection_name = "peer_selection"
__purchase_order_collection = get_database_connection(__purchase_order_collection_name)


class PurchaseOrder:
    def __init__(
        self, requested_amount, buyer_id, buyer_username, buyer_coordinate
    ) -> None:
        self.buyer_id = buyer_id
        self.buyer_username = buyer_username
        self.buyer_coordinate = buyer_coordinate
        self.requested_amount = requested_amount
        self.candidates = []

    def __calculate_distance(self, coord1, coord2):
        lat1, lon1 = map(float, coord1.split())
        lat2, lon2 = map(float, coord2.split())
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers

    def sortCandidatesByDistance(self, peers):
        for seller in peers:
            energy_balance = int(seller.current_energy)
            distance = self.__calculate_distance(
                self.buyer_coordinate, seller.geo_coordinate
            )

            self.candidates.append(
                Candidate(seller.id, seller.username, distance, energy_balance)
            )

        self.candidates.sort(key=lambda c: c.distance)

    def isTotalEnergySufficient(self) -> bool:
        available_energies = map(lambda c: c.available_energy, self.candidates)
        total_available_energy = sum(available_energies)
        return total_available_energy < self.requested_amount

    def decideProviderType(self):
        first_candidate_energy = self.candidates[0].available_energy
        self.provider_type = (
            "SINGLE" if first_candidate_energy >= self.requested_amount else "MULTIPLE"
        )

    def select_single_provider_candidate(self):
        candidate = self.candidates[0]
        candidate.energy_taken = self.requested_amount
        candidate.status = "PENDING"
        return candidate

    def select_multiple_provider_candidates(self):
        selected_candidates = []
        total_energy_taken = 0
        for candidate in self.candidates:
            if total_energy_taken >= self.requested_amount:
                break

            energy_needs = self.requested_amount - total_energy_taken
            energy_balance = candidate.available_energy
            energy_taken = min(energy_needs, energy_balance)

            candidate.energy_taken = energy_taken
            candidate.status = "PENDING"

            selected_candidates.append(candidate)
            total_energy_taken += energy_taken

        return selected_candidates

    def save(self):
        if self.id is None:
            result = __purchase_order_collection.insert_one(self.toJson())
            self.id = result.inserted_id
        else:
            __purchase_order_collection.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": self.toJson()},
            )

    def toJson(self):
        return {
            "buyer_id": self.buyer_id,
            "buyer_username": self.buyer_username,
            "buyer_coordinates": self.buyer_coordinate,
            "requested_amount": self.requested_amount,
            "provider_type": self.provider_type,
            "candidate": Candidate.toJsonArray(self.candidates),
        }

    # class methods

    def fromJson(json):
        return PurchaseOrder(
            json["_id"],
            json["buyer_id"],
            json["buyer_username"],
            json["buyer_coordinates"],
            json["requested_amount"],
            json["provider_type"],
            Candidate.fromJsonArray(json["candidate"]),
        )

    def getById(id):
        result = __purchase_order_collection.find_one({"_id": ObjectId(id)})
        return PurchaseOrder(result)

    def __update_candidate_on_response(purchase_id, seller_id, status):
        __purchase_order_collection.update_one(
            {"_id": ObjectId(purchase_id), "candidate.user_id": seller_id},
            {"$set": {"candidate.$.status": status}},
        )

    def update_candidate_decline_request(purchase_id, seller_id):
        PurchaseOrder.__update_candidate_on_response(purchase_id, seller_id, "DECLINED")

    def update_candidate_approve_request(purchase_id, seller_id):
        PurchaseOrder.__update_candidate_on_response(purchase_id, seller_id, "APPROVED")


class Candidate:
    def __init__(self, seller_id, seller_username, distance, available_energy) -> None:
        self.seller_id = seller_id
        self.seller_username = seller_username
        self.distance = distance
        self.available_energy = available_energy
        self.energy_taken = 0

    def toJson(self):
        return {
            "user_id": self.seller_id,
            "username": self.seller_username,
            "distance": self.distance,
            "availabel_energy": self.available_energy,
            "energy_taken": self.energy_taken,
        }

    def __fromJson(json) -> None:
        return Candidate(
            json["seller_id"],
            json["seller_username"],
            json["distance"],
            json["available_energy"],
            json["energy_taken"],
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
