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
generated_energy = sys.argv[3]
receiver = None

if len(sys.argv) >= 5:
    receiver = sys.argv[4]

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

## loop per menit
# beban = baca file beban
# kirim ke server via peers.py send_energy_update(peer_id, beban, beban + generated_energy)

def main_loop():
    for _ in range(10):  # loop per minute
        try:
            with open("beban.txt", "r") as file:
                current_load_str = file.readlines()
                for line in current_load_str:
                    
                    __LOG.info(f"Read from file: Beban content: {line}")
                    current_load = float(line)
                    __LOG.info(f"current_load: {current_load}")

                    peer.send_energy_update(peer_id, current_load, float(generated_energy))
                    
                    time.sleep(60)
        except FileNotFoundError:
            __LOG.warning("Beban file not found.")
        except ValueError:
            __LOG.warning("Invalid content in beban file.")

        

    
sender_thread = Thread(target= main_loop)
sender_thread.start()

#main_loop()


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

