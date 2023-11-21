FROM python:3.9.6-alpine3.14

WORKDIR /opt/powerchain/

ENV MONGO_HOST=localhost
ENV ETHEREUM_HOST=localhost
ENV MQTT_HOST=localhost
ENV MQTT_CLIENT_ID=powerchain-server-1

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

ENTRYPOINT python app.py $MONGO_HOST $ETHEREUM_HOST $MQTT_HOST $MQTT_CLIENT_ID