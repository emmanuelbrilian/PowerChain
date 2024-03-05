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

    def __on_message(self, x, y, message):
        self.__LOG.info(
            f"Received {message.payload.decode()} from topic {message.topic}"
        )
        if message.topic == f"{self.id}_energy_transfer_request":
            self.__send_progress(message)
        elif message == f"{self.id}_energy_transfer_progress":
            self.__send_ack(message)

    ### PEERS RECEIVE TRANSFER REQUEST MESSAGE ###
    def init_receive(self):
        if not self.__is_listening:
            self.__is_listening = True
            topic = f"{self.id}_energy_transfer_request"
            self.__mqtt_client.subscribe(topic)
            self.__mqtt_client.on_message = self.__on_message
            self.__LOG.info(f"Listening to {topic}")

    def __send_progress(self, message):
        decoded_message = str(message.payload.decode("utf-8"))
        json_message = json.loads(decoded_message)
        purchase_id = json_message["purchase_id"]
        contract = json_message["contract"]
        seller_username = json_message['sender_username']
        receiver = json_message['receiver']
        self.__LOG.info(f"Received message {purchase_id} from topic {message.topic}")

        payload = {
            "type": "energy_transfer_progress",
            "purchase_id": purchase_id,
            "contract": contract,
            "seller_username": seller_username
        }
        message = json.dumps(payload)
        topic = f"{receiver}_energy_transfer_progress"
        result = self.__mqtt_client.publish(topic, message)
        status = result[0]
        if status != 0:
            self.__LOG.error(f"Failed publishing to topic {topic}, status: {status}")
        else:
            self.__LOG.info(f"Message {purchase_id} was published into topic '{topic}'")
        
    ### PEERS RECEIVE TRANSFER REQUEST PROGRESS MESSAGE ###
    def init_receive_progress(self):
        if not self.__is_listening_progress:
            self.__is_listening_progress = True
            topic = f"{self.id}_energy_transfer_progress"
            self.__mqtt_client.subscribe(topic)
            self.__mqtt_client.on_message = self.__on_message
            self.__LOG.info(f"Listening to {topic}")

    def __send_ack(self, message):
        decoded_message = str(message.payload.decode("utf-8"))
        json_message = json.loads(decoded_message)
        purchase_id = json_message["purchase_id"]
        contract = json_message["contract"]
        seller_username = json_message['seller_username']
        self.__LOG.info(f"Received message {purchase_id} from topic {message.topic}")

        payload = {
            "type": "energy_transfer_request_acknowledgment",
            "purchase_id": purchase_id,
            "contract": contract,
            "seller_username": seller_username
        }
        message = json.dumps(payload)
        topic = f"energy_transfer_request_ack"
        result = self.__mqtt_client.publish(topic, message)
        status = result[0]
        if status != 0:
            self.__LOG.error(f"Failed publishing to topic {topic}, status: {status}")
        else:
            self.__LOG.info(f"Message {purchase_id} was published into topic '{topic}'")

    ### PEERS SENDING ENERGY UPDATE MESSAGE ###
    def send_energy_update(self, peer_id, current_load, generated_energy):
        payload = {
            "type": "energy_update",
            "peer_id": peer_id,
            "current_load": current_load,
            "total_load": current_load + generated_energy
        }
        message = json.dumps(payload)
        topic = "energy_update"
        result = self.__mqtt_client.publish(topic, message)
        status = result[0]
        if status != 0:
            self.__LOG.error(f"Failed publishing to topic {topic}, status: {status}")
        else:
            self.__LOG.info(f"Energy update sent: Peer_ID={peer_id}, Current Load={current_load}, Total Load={current_load + generated_energy}")

    ######### FOR TESTING #########
            
    def init_receive_ack(self):
        if not self.__is_listening_ack:
            self.__is_listening_ack = True
            topic = f"energy_transfer_request_ack"
            self.__mqtt_client.subscribe(topic)
            self.__mqtt_client.on_message = self.__on_message
            self.__LOG.info(f"Listening to {topic}")

    def send(self, message, receiver):
        msg = json.dumps(message)
        topic = f"{receiver}_energy_transfer_request"
        result = self.__mqtt_client.publish(topic, msg)
        status = result[0]
        if status != 0:
            self.__LOG.error(f"Failed publishing to topic {topic}, status: {status}")
        else:
            self.__LOG.info(f"Message {message} was published into topic '{topic}'")
