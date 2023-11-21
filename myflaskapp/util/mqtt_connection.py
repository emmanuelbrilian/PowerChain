import logging
import time

import paho.mqtt.client as mqtt

__LOG = logging.getLogger("MqttConnection")

__client_id = "powerchain_server_1"
__mqtt_host = "localhost"
__mqtt_port = 1883

class __MQTTConnection:
    client: mqtt.Client = None
    is_connected = False

def init_mqtt():
    get_mqtt_connection()

def get_mqtt_connection():
    if __MQTTConnection.client == None:
        __MQTTConnection.client = __connect_mqtt()
    return __MQTTConnection.client


def __connect_mqtt():
    __LOG.info("Connecting to broker")

    try:
        client = mqtt.Client(__client_id)
        client.on_connect = __on_connect
        client.on_disconnect = __on_disconnect
        client.username_pw_set(username="admin", password="powerchain")
        client.connect_async(__mqtt_host, __mqtt_port)
        client.loop_start()
        time.sleep(5)

        return client
    except Exception as e:
        __LOG.error("Cannot connect to broker")


def __on_connect(client, user_data, flags, response_code):
    if response_code == 0:
        __MQTTConnection.is_connected = True
        __LOG.info("Connected to broker")
    else:
        __LOG.error(f"Failed to connect to broker with response code {response_code}")


def __on_disconnect(client, user_data, response_code):
    __MQTTConnection.is_connected = False
    __LOG.info(f"Disconnected. Reason: {str(response_code)}")
