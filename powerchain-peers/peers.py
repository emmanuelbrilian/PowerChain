import logging
import json

from mqtt_connection import connect_mqtt, is_connected


class Peer:
    def __init__(self, id) -> None:
        self.__LOG = logging.getLogger("Peer")
        self.__is_listening = False
        self.__is_listening_ack = False
        self.id = id
        self.__mqtt_client = connect_mqtt(id)

    def send_electricity(self, message):
        decoded_message = str(message.payload.decode("utf-8"))
        json_message = json.loads(decoded_message)
        purchase_id = json_message["purchase_id"]
        contract = json_message["contract"]
        self.__LOG.info(f"Received message {purchase_id} from topic {message.topic}")

        # Because of simulation, this peer was assumed will send the electricity automatically
        # So it just need to send acknowledgement message to server
        self.send_ack(purchase_id=purchase_id, contract=contract)

    def send(self, message, receiver):
        msg = json.dumps(message)
        topic = f"{receiver}_energy_transfer_request"
        result = self.__mqtt_client.publish(topic, msg)
        status = result[0]
        if status != 0:
            self.__LOG.error(f"Failed publishing to topic {topic}, status: {status}")
        else:
            self.__LOG.info(f"Message {message} was published into topic '{topic}'")

    def init_receive(self):
        if not self.__is_listening:
            self.__is_listening = True
            topic = f"{self.id}_energy_transfer_request"
            self.__mqtt_client.subscribe(topic)
            self.__mqtt_client.on_message = self.__on_message
            self.__LOG.info(f"Listening to {topic}")

    def send_ack(self, purchase_id, contract):
        payload = {
            "type": "energy_transfer_request_acknowledgment",
            "purchase_id": purchase_id,
            "contract": contract
        }
        message = json.dumps(payload)
        topic = f"energy_transfer_request_ack"
        result = self.__mqtt_client.publish(topic, message)
        status = result[0]
        if status != 0:
            self.__LOG.error(f"Failed publishing to topic {topic}, status: {status}")
        else:
            self.__LOG.info(f"Message {purchase_id} was published into topic '{topic}'")

    def init_receive_ack(self):
        if not self.__is_listening_ack:
            self.__is_listening_ack = True
            topic = f"energy_transfer_request_ack"
            self.__mqtt_client.subscribe(topic)
            self.__mqtt_client.on_message = self.__on_message
            self.__LOG.info(f"Listening to {topic}")

    def __on_message(self, x, y, message):
        self.__LOG.info(
            f"Received {message.payload.decode()} from topic {message.topic}"
        )
        if message.topic != "energy_transfer_request_ack":
            self.send_electricity(message)
