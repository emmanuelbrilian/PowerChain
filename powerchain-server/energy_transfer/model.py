import json
import logging

from user.model import get_by_username, save as save_user
from purchase_order.model import get_po_by_id, save_po
from util.mqtt_connection import get_mqtt_connection
from util.ethereum_connection import get_ethereum_connetion, get_trade_contract_abi

__LOG = logging.getLogger("EnergyTransferModel")

__transfer_acknowledge_topic = "energy_transfer_request_ack"


class __Listener:
    is_listening = False


class EnergyTransfer:
    def __init__(
        self, sender, receiver, transfer_amount, purchase_id, contract, sender_username
    ) -> None:
        self.sender = sender
        self.receiver = receiver
        self.transfer_amount = transfer_amount
        self.purchase_id = purchase_id
        self.contract = contract
        self.sender_username = sender_username

    def to_json(self):
        return {
            "type": "energy_transfer_request",
            "sender": self.sender,
            "receiver": self.receiver,
            "transfer_amount": self.transfer_amount,
            "purchase_id": self.purchase_id,
            "contract": self.contract,
            "sender_username": self.sender_username,
        }


def send_energy_transfer_request(energy_transfer: EnergyTransfer):
    message = json.dumps(energy_transfer.to_json())
    topic = f"{energy_transfer.sender}_energy_transfer_request"
    result = get_mqtt_connection("transfer_request").publish(topic, message)
    status = result[0]
    if status != 0:
        __LOG.error(f"Failed publishing to topic {topic}, status: {status}")
    else:
        __LOG.info(f"Message {message} was published into topic '{topic}'")


def init_energy_transfer_ack_listener():
    mqtt_client = get_mqtt_connection("transfer_ack")

    if not __Listener.is_listening:
        __Listener.is_listening = True
        mqtt_client.subscribe(__transfer_acknowledge_topic)
        mqtt_client.on_message = __on_message
        __LOG.info(f"Listening to {__transfer_acknowledge_topic}")


def __on_message(client, user_data, message):
    decoded_message = str(message.payload.decode("utf-8"))
    __LOG.info(
        f"Receiving message from topic '{message.topic}' with payload '{decoded_message}'"
    )

    json_message = json.loads(decoded_message)
    purchase_id = json_message["purchase_id"]
    contract = json_message["contract"]
    seller_username = json_message["seller_username"]
    po = get_po_by_id(purchase_id)
    buyer = get_by_username(po.buyer_username)
    seller = get_by_username(seller_username)

    po_candidate = po.approve_candidate(seller.id)

    w3 = get_ethereum_connetion()
    abi = get_trade_contract_abi()
    trade = w3.eth.contract(address=contract, abi=abi)

    w3.eth.defaultAccount = buyer.bcaddress
    price = trade.functions.getPrice().call()
    __LOG.info(f"Price is: {price}")

    buyer_txn = {
        "from": buyer.bcaddress,
        "to": seller.bcaddress,
        "value": price,
        "gas": 1000000,
    }

    buyer_txn_hash = trade.functions.buy().transact(buyer_txn)
    buyer_txn_receipt = w3.eth.wait_for_transaction_receipt(buyer_txn_hash)

    __LOG.info(f"Completed transaction: {buyer_txn_receipt}")

    seller.current_energy -= po_candidate.requested_energy
    seller.energy_purchased += po_candidate.requested_energy
    save_user(seller)

    buyer.current_energy += po_candidate.requested_energy
    buyer.energy_sold += po_candidate.requested_energy
    save_user(buyer)

    save_po(po)
