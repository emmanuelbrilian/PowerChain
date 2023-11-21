import logging
import time

import paho.mqtt.client as mqtt

__LOG = logging.getLogger("MqttConnection")

class MQTTConnection:
    client: mqtt.Client = None
    is_connected = False
    mqtt_host = "localhost"
    client_id = "powerchain_server_1"
    mqtt_port = 1883

def init_mqtt(mqtt_host, client_id):
    MQTTConnection.mqtt_host = mqtt_host
    MQTTConnection.is_connected = False
    MQTTConnection.client_id = client_id

def get_mqtt_connection():
    if not MQTTConnection.is_connected:
        MQTTConnection.client = __connect_mqtt()
    return MQTTConnection.client


def __connect_mqtt():
    __LOG.info(f"Connecting to broker at: {MQTTConnection.mqtt_host}:{MQTTConnection.mqtt_port}")

    try:
        client = mqtt.Client(MQTTConnection.client_id)
        client.on_connect = __on_connect
        client.on_disconnect = __on_disconnect
        client.username_pw_set(username="admin", password="powerchain")
        client.connect_async(MQTTConnection.mqtt_host, MQTTConnection.mqtt_port)
        client.loop_start()
        time.sleep(5)

        return client
    except Exception as e:
        __LOG.error("Cannot connect to broker")


def __on_connect(client, user_data, flags, response_code):
    if response_code == 0:
        MQTTConnection.is_connected = True
        __LOG.info(f"Connected to broker at: {MQTTConnection.mqtt_host}:{MQTTConnection.mqtt_port}")
    else:
        __LOG.error(f"Failed to connect to broker with response code {response_code}")


def __on_disconnect(client, user_data, response_code):
    MQTTConnection.is_connected = False
    __LOG.info(f"Disconnected. Reason: {str(response_code)}")
