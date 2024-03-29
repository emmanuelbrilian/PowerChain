import logging

from bson import ObjectId
from geopy.distance import geodesic

from util.db_connection import get_collection


class Candidate:
    def __init__(
        self,
        seller_id,
        seller_username,
        distance,
        available_energy,
        requested_energy=0,
        status=None,
    ) -> None:
        self.seller_id = seller_id
        self.seller_username = seller_username
        self.distance = distance
        self.available_energy = available_energy
        self.requested_energy = requested_energy
        self.status = status

    def decline(self):
        self.status = "DECLINED"

    def approve(self):
        self.status = "APPROVED"

    def to_json(self):
        return {
            "seller_id": self.seller_id,
            "seller_username": self.seller_username,
            "distance": self.distance,
            "available_energy": self.available_energy,
            "requested_energy": self.requested_energy,
            "status": self.status,
        }

class PurchaseOrder:
    __LOG = logging.getLogger("PurchaseOrder")
    
    def __init__(
        self,
        requested_amount,
        buyer_id,
        buyer_username,
        buyer_coordinates,
        provider_type=None,
        candidates=[],
        status="ON_GOING",
        id=None,
    ) -> None:
        self.id = id
        self.buyer_id = buyer_id
        self.buyer_username = buyer_username
        self.buyer_coordinates = buyer_coordinates
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
                self.buyer_coordinates, seller.geo_coordinates
            )

            candidates.append(
                Candidate(seller.id, seller.username, distance, energy_balance)
            )

        self.__LOG.debug(f"Found {len(candidates)} candidates")
        candidates.sort(key=lambda c: c.distance)
        self.candidates = candidates

    def isTotalEnergySufficient(self) -> bool:
        available_energies = map(lambda c: c.available_energy, self.candidates)
        total_available_energy = sum(available_energies)
        self.__LOG.debug(
            f"Total available energy: {total_available_energy}, requested energy: {self.requested_amount}"
        )
        return total_available_energy < self.requested_amount

    def decideProviderType(self):
        first_candidate_energy = self.candidates[0].available_energy
        self.provider_type = (
            "SINGLE" if first_candidate_energy >= self.requested_amount else "MULTIPLE"
        )

    def isSingleProvider(self) -> bool:
        return self.provider_type == "SINGLE"

    def isMultipleProvider(self) -> bool:
        return self.provider_type == "MULTIPLE"

    def select_single_provider_candidate(self):
        candidate = next(filter(lambda c: c.status == None, self.candidates))
        candidate.requested_energy = self.requested_amount
        candidate.status = "PENDING"
        return candidate

    def __initialized_candidates_status(self):
        pending_candidates = filter(
            lambda c: c.status == "PENDING",
            self.candidates,
        )
        for pc in pending_candidates:
            pc.status = None
            pc.requested_energy = 0

    def select_multiple_provider_candidates(self):
        selected_candidates = []
        total_energy = 0

        self.__initialized_candidates_status()

        while total_energy < self.requested_amount:
            candidate = next(
                filter(
                    lambda c: c.status == None,
                    self.candidates,
                )
            )

            energy_needs = self.requested_amount - total_energy
            energy_balance = candidate.available_energy
            requested_energy = min(energy_needs, energy_balance)

            candidate.requested_energy = requested_energy
            candidate.status = "PENDING"

            selected_candidates.append(candidate)
            total_energy += requested_energy

        return selected_candidates

    def decline_candidate(self, seller_id):
        candidate = next(filter(lambda c: c.seller_id == seller_id, self.candidates))
        candidate.decline()

    def approve_candidate(self, seller_id) -> Candidate:
        candidate: Candidate = next(filter(lambda c: c.seller_id == seller_id, self.candidates))
        candidate.approve()
        return candidate

    def to_json(self):
        return {
            "_id": self.id,
            "buyer_id": self.buyer_id,
            "buyer_username": self.buyer_username,
            "buyer_coordinates": self.buyer_coordinates,
            "requested_amount": self.requested_amount,
            "provider_type": self.provider_type,
            "status": self.status,
            "candidates": to_candidates_json(self.candidates),
        }



__purchase_order_collection_name = "purchase_orders"

def __get_collection():
    return get_collection(__purchase_order_collection_name)
    
def save_po(purchase_order: PurchaseOrder):
    collection = __get_collection()
    data = purchase_order.to_json()
    del data["_id"]

    if purchase_order.id is None:
        result = collection.insert_one(data)
        purchase_order.id = result.inserted_id
    else:
        collection.update_one(
            {"_id": ObjectId(purchase_order.id)},
            {"$set": data},
        )


def get_po_by_id(id):
    result = __get_collection().find_one({"_id": ObjectId(id)})
    return __from_po_json(result)


def __from_po_json(json):
    return PurchaseOrder(
        id=str(json["_id"]),
        buyer_id=json["buyer_id"],
        buyer_username=json["buyer_username"],
        buyer_coordinates=json["buyer_coordinates"],
        requested_amount=json["requested_amount"],
        provider_type=json["provider_type"],
        status=json["status"],
        candidates=__from_candidates_json(json["candidates"]),
    )


def __from_candidates_json(json):
    candidates = []
    for j in json:
        candidates.append(__from_candidate_json(j))
    return candidates


def __from_candidate_json(json) -> None:
    return Candidate(
        seller_id=json["seller_id"],
        seller_username=json["seller_username"],
        distance=json["distance"],
        available_energy=json["available_energy"],
        requested_energy=json["requested_energy"],
        status=json["status"],
    )


def to_candidates_json(candidates):
    json = []
    for c in candidates:
        json.append(c.to_json())
    return json
