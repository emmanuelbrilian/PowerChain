import logging
import time

import paho.mqtt.client as mqtt

__LOG = logging.getLogger("MqttConnection")


class MQTTConnection:
    client = None
    is_connected = False
    host = "localhost"
    port = 1883
    client_id = "powerchain_peer_1"


def init_mqtt(mqtt_host):
    MQTTConnection.host = mqtt_host
    MQTTConnection.is_connected = False
    MQTTConnection.client = None


def connect_mqtt(client_id):
    __LOG.info(f"Connecting to broker at: {MQTTConnection.host}:{MQTTConnection.port}")
    MQTTConnection.client_id = client_id

    if MQTTConnection.is_connected:
        __LOG.info("Using current connection")
        return MQTTConnection.client

    try:
        MQTTConnection.client = mqtt.Client(MQTTConnection.client_id)
        MQTTConnection.client.on_connect = __on_connect
        MQTTConnection.client.on_disconnect = __on_disconnect
        MQTTConnection.client.username_pw_set(username="admin", password="powerchain")
        MQTTConnection.client.connect_async(MQTTConnection.host, MQTTConnection.port)
        MQTTConnection.client.loop_start()
        time.sleep(5)

        return MQTTConnection.client
    except Exception as e:
        __LOG.error("Cannot connect to broker")


def __on_connect(client, user_data, flags, response_code):
    if response_code == 0:
        __LOG.info(f"Connected to broker at {MQTTConnection.host}:{MQTTConnection.port}")
        MQTTConnection.is_connected = True
    else:
        __LOG.error(f"Failed to connect to broker with response code {response_code}")


def __on_disconnect(client, user_data, response_code):
    __LOG.info(f"Disconnected. Reason: {str(response_code)}")
    MQTTConnection.is_connected = False


def is_connected():
    return MQTTConnection.is_connected
