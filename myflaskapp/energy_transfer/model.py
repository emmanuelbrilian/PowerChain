import logging
from util.mqtt_connection import connect_mqtt


class EnergyTransfer:
    __LOG = logging.getLogger("EnergyTransferModel")

    __mqtt_client = connect_mqtt()

    __transfer_topic = "powerchain.transfer_energy"

    __transfer_ack_topic = "powerchain.transfer_energy_ack"

    def __init__(self, sender, receiver, transfer_amount, purchase_id) -> None:
        self.sender = sender
        self.receiver = receiver
        self.transfer_amount = transfer_amount
        self.purchase_id = purchase_id

    def __to_json(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "transfer_amount": self.transfer_amount,
            "purchase_id": self.purchase_id,
        }

    def send(self):
        message = str(self.__to_json())
        result = self.__mqtt_client.publish(self.__transfer_topic, message)
        status = result[0]
        if status != 0:
            self.__LOG.error(
                f"Failed publishing to topic {self.__transfer_topic}, status: {status}"
            )
        else:
            self.__LOG.info(
                f"Message was published into topic '{self.__transfer_topic}'"
            )

    def init_receive():
        EnergyTransfer.__mqtt_client.subscribe(EnergyTransfer.__transfer_ack_topic)
        EnergyTransfer.__mqtt_client.on_message = EnergyTransfer.__on_message

    def __on_message(client, user_data, message):
        EnergyTransfer.__LOG.info(
            f"Receiving message from topic '{message.topic}' with payload '{message.payload}'"
        )

        # execute contract
