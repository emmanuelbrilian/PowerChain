import logging
import time

from mqtt_connection import MQTTConnection, init_mqtt
from peers import Peer

logging.basicConfig(level=logging.DEBUG)

__LOG = logging.getLogger("App")
__LOG.info("Start peer")

init_mqtt()
peer = Peer(id="peer1")

try:
    while True:
        peer.init_receive(
            lambda x, y, message: print(f"received message")
        )
        # time.sleep(1)
except KeyboardInterrupt:
    __LOG.info("Stopping peer")
    MQTTConnection.client.loop_stop()
