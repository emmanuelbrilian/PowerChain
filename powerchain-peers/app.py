import logging
import sys
import time
from threading import Thread

from mqtt_connection import MQTTConnection, init_mqtt
from peers import Peer

logging.basicConfig(level=logging.DEBUG)

__LOG = logging.getLogger("App")

peer_id = sys.argv[1]
mqtt_host = sys.argv[2]
receiver = None

if len(sys.argv) >= 4:
    receiver = sys.argv[3]

__LOG.info(f"Starting {peer_id}")

init_mqtt(mqtt_host=mqtt_host)
peer = Peer(id=peer_id)


def receiver_func():
    try:
        while True:
            peer.init_receive()
    except KeyboardInterrupt:
        __LOG.info(f"Stopping {peer_id}")
        MQTTConnection.client.loop_stop()


receiver_thread = Thread(target=receiver_func)
receiver_thread.start()

# If peer is sender
# Only for testing
if receiver != None:

    def sender_func():
        peer.init_receive_ack()
        for x in range(10):
            message = {
                "type": "energy_transfer_request",
                "sender": peer_id,
                "receiver": receiver,
                "purchase_id": f"purchase_{x}",
            }

            peer.send(message, receiver)
            time.sleep(2)

    sender_thread = Thread(target=sender_func)
    sender_thread.start()
