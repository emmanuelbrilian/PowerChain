import logging
import time

import paho.mqtt.client as mqtt

__LOG = logging.getLogger("MqttConnection")

__server = "localhost"
__server_port = 1883
__client_id = "powerchain_peer_2"


def init_mqtt():
    MQTTConnection.is_connected = False
    MQTTConnection.client = None
    connect_mqtt()


def connect_mqtt():
    __LOG.info("Connecting to broker")

    if MQTTConnection.is_connected:
        __LOG.info("Using current connection")
        return MQTTConnection.__client

    try:
        MQTTConnection.__client = mqtt.Client(__client_id)
        MQTTConnection.__client.on_connect = __on_connect
        MQTTConnection.__client.on_disconnect = __on_disconnect
        MQTTConnection.__client.username_pw_set(username="admin", password="powerchain")
        MQTTConnection.__client.connect_async(__server, __server_port)
        MQTTConnection.__client.loop_start()
        time.sleep(5)

        return MQTTConnection.__client
    except Exception as e:
        __LOG.error("Cannot connect to broker")


def __on_connect(client, user_data, flags, response_code):
    if response_code == 0:
        __LOG.info("Connected to broker")
        MQTTConnection.is_connected = True
    else:
        __LOG.error(f"Failed to connect to broker with response code {response_code}")


def __on_disconnect(client, user_data, response_code):
    __LOG.info(f"Disconnected. Reason: {str(response_code)}")
    MQTTConnection.is_connected = False
    MQTTConnection.__client.loop_stop()

def is_connected():
    return MQTTConnection.is_connected

class MQTTConnection:
    client = None
    is_connected = False
