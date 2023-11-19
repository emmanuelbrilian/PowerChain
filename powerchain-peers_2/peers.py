import logging
from mqtt_connection import connect_mqtt, is_connected

import json


class EnergyTransfer:
    __LOG = logging.getLogger("EnergyTransferModel")
    __mqtt_client = connect_mqtt()

    def __init__(self, peer_id, receiver, purchase_id) -> None:
        self.sender = peer_id
        self.receiver = receiver
        self.purchase_id = purchase_id

    def __to_json(self):
        return {
            "type": "energy_transfer_request",
            "sender": self.sender,
            "receiver": self.receiver,
            "purchase_id": self.purchase_id
        }

    def send(self):
        message = json.dumps(self.__to_json())
        topic = f"{self.receiver}_energy_transfer_request"
        result = self.__mqtt_client.publish(topic, message)
        status = result[0]
        if status != 0:
            self.__LOG.error(
                f"Failed publishing to topic {topic}, status: {status}"
            )
        else:
            self.__LOG.info(
                f"Message was published into topic '{topic}'"
            )

    def init_receive(self, callback):
        if not is_connected():
            topic = f"{self.sender}/energy_transfer_ack"
            self.__mqtt_client.subscribe(topic)
            self.__mqtt_client.on_message = callback
