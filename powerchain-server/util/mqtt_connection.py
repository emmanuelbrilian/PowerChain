import logging
import time

import paho.mqtt.client as mqtt

__LOG = logging.getLogger("MqttConnection")

class MQTTConnection:
    clients = {}
    mqtt_host = "localhost"
    client_id = "powerchain_server_1"
    mqtt_port = 1883

def init_mqtt(mqtt_host, client_id):
    MQTTConnection.mqtt_host = mqtt_host
    MQTTConnection.client_id = client_id

def get_mqtt_connection(connection_id):
    if MQTTConnection.clients.get(connection_id) == None:
        new_client = __connect_mqtt(f"{MQTTConnection.client_id}.{connection_id}")
        MQTTConnection.clients[connection_id] = new_client
    return MQTTConnection.clients.get(connection_id)


def __connect_mqtt(client_id):
    __LOG.info(f"Connecting to broker at: {MQTTConnection.mqtt_host}:{MQTTConnection.mqtt_port} for client {client_id}")

    try:
        client = mqtt.Client(client_id)
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
