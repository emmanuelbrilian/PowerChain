import logging
import json

from mqtt_connection import connect_mqtt, is_connected

class Peer:
    def __init__(self, id) -> None:
        self.__LOG = logging.getLogger("Peer")
        self.__is_listening = False
        self.id = id
        self.__mqtt_client = connect_mqtt()


    def send_electricity(self, message):
        print(f"Received")
        # decoded_message=str(message.payload.decode("utf-8"))
        # print(f"Received `{decoded_message}`")
        # msg=json.loads(decoded_message)
        # print(f"Received `{msg}`")
        # self.send_ack()


    def init_receive(self, callback):
        if not self.__is_listening:
            self.__is_listening = True
            topic = f"{self.id}_energy_transfer_request"
            self.__mqtt_client.subscribe(topic)
            self.__mqtt_client.on_message = callback
            self.__LOG.info(f"Listening to {topic}")


    def send_ack(self, purchase_id):
        payload = {
            "type": "energy_transfer_request_acknowledgment",
            "purchase_id": purchase_id,
        }
        message = json.dumps(payload)
        topic = f"energy_transfer_request_ack"
        result = self.__mqtt_client.publish(topic, message)
        status = result[0]
        if status != 0:
            self.__LOG.error(f"Failed publishing to topic {topic}, status: {status}")
        else:
            self.__LOG.info(f"Message was published into topic '{topic}'")
