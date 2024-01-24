import logging
import sys
import time
from threading import Thread

from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect

from util.ethereum_connection import init_ethereum
from util.db_connection import init_mongo
from util.mqtt_connection import get_mqtt_connection, init_mqtt
from energy_transfer.model import init_ack_listener
from user.model import init_energyupdate_listener
from purchase_order.service import purchase_order_service
from user.service import user_service
from notification.service import notification_service

logging.basicConfig(level=logging.DEBUG)

__LOG = logging.getLogger("App")
__LOG.info("Start server")


mongo_host = "localhost"
if len(sys.argv) >= 2:
    mongo_host = sys.argv[1]

ethereum_host = "localhost"
if (len(sys.argv) >= 3):
    ethereum_host = sys.argv[2]

mqtt_host = "localhost"
if len(sys.argv) >= 4:
    mqtt_host = sys.argv[3]

mqtt_client_id = "powerchain-server-2"
if len(sys.argv) >= 5:
    mqtt_client_id = sys.argv[4]

init_mongo(mongo_host)
init_ethereum(ethereum_host)
init_mqtt(mqtt_host, mqtt_client_id)

def receiver_func():
    try:
        
        while True:
            init_ack_listener()
    except KeyboardInterrupt:
        get_mqtt_connection().loop_stop()
        __LOG.info(f"Stopping mqtt connection")


receiver_thread = Thread(target=receiver_func)
receiver_thread.start()

time.sleep(3)
def receiver_energyupdate():
    try:
        
        while True:
            init_energyupdate_listener()
    except KeyboardInterrupt:
        get_mqtt_connection().loop_stop()
        __LOG.info(f"Stopping mqtt connection")


receiver_energyupdate_thread = Thread(target=receiver_energyupdate)
receiver_energyupdate_thread.start()



app = Flask(__name__)
app.secret_key = "secret123"
app.register_blueprint(purchase_order_service)
app.register_blueprint(user_service)
app.register_blueprint(notification_service)
CSRFProtect(app)


# Index
@app.route("/")
def index():
    return render_template("home.html")


# About
@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.secret_key = "secret123"
    app.run(host="0.0.0.0", port=5001)
