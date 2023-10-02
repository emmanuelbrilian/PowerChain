import logging

from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect

from util.ethereum_connection import init_ethereum
from util.db_connection import init_mongo
from util.mqtt_connection import init_mqtt

logging.basicConfig(level=logging.DEBUG)

__LOG = logging.getLogger("App")
__LOG.info("Start server")

init_mongo()
init_mqtt()
init_ethereum()

from purchase_order.service import purchase_order_service
from user.service import user_service
from notification.service import notification_service

# pass email Pc_123456
app = Flask(__name__)
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
    app.run(port=5001, debug=True)
