import json
import logging
from util.mqtt_connection import MQTTConnection, get_mqtt_connection

__LOG = logging.getLogger("EnergyTransferModel")

__transfer_acknowledge_topic = "energy_transfer_request_ack"

class __Listener:
    is_listening = False

class EnergyTransfer:

    def __init__(self, sender, receiver, transfer_amount, purchase_id) -> None:
        self.sender = sender
        self.receiver = receiver
        self.transfer_amount = transfer_amount
        self.purchase_id = purchase_id

    def to_json(self):
        return {
            'type': 'energy_transfer_request',
            'sender': self.sender,
            'receiver': self.receiver,
            'transfer_amount': self.transfer_amount,
            'purchase_id': self.purchase_id,
        }

def send_energy_transfer_request(energy_transfer: EnergyTransfer):
    message = json.dumps(energy_transfer.to_json())
    topic = f"{energy_transfer.sender}_energy_transfer_request"
    result = get_mqtt_connection().publish(topic, message)
    status = result[0]
    if status != 0:
        __LOG.error(
            f"Failed publishing to topic {topic}, status: {status}"
        )
    else:
        __LOG.info(
            f"Message {message} was published into topic '{topic}'"
        )


def init_ack_listener():
    mqtt_client = get_mqtt_connection()

    if not __Listener.is_listening:
        __Listener.is_listening = True
        mqtt_client.subscribe(__transfer_acknowledge_topic)
        mqtt_client.on_message = __on_message
        __LOG.info(f"Listening to {__transfer_acknowledge_topic}")

def __on_message(client, user_data, message):
    __LOG.info(
        f"Receiving message from topic '{message.topic}' with payload '{message.payload.decode()}'"
    )

    # TODO execute contract
