from threading import Thread
import logging
import time

from mqtt_connection import init_mqtt
from peers import EnergyTransfer

logging.basicConfig(level=logging.DEBUG)

__LOG = logging.getLogger("App")
__LOG.info("Start peer")

init_mqtt()
energyTransfer = EnergyTransfer(peer_id="peer2", receiver="peer1", purchase_id="purchase_001")

for x in range(10):
  energyTransfer.send()
  time.sleep(2)
