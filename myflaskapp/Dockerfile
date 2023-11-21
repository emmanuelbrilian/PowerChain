FROM python:3.9.6-alpine3.14

WORKDIR /opt/powerchain/

ENV MQTT_HOST=localhost

ADD energy_transfer energy_transfer
ADD notification notification
ADD purchase_order purchase_order
ADD static static
ADD templates templates
ADD user user
ADD util util
ADD app.py app.py

RUN pip install --upgrade pip
RUN pip install flask flask_wtf web3 pymongo paho_mqtt geopy passlib

ENTRYPOINT python app.py $MQTT_HOST