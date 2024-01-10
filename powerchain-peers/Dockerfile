FROM python:3.9.6-alpine3.14

ENV PEER_ID=peer1
ENV MQTT_HOST=localhost
ENV GENERATED_ENERGY=0

WORKDIR /opt/powerchain/

ADD app.py .
ADD mqtt_connection.py .
ADD peers.py .

RUN pip install --upgrade pip
RUN pip install paho-mqtt

ENTRYPOINT python app.py $PEER_ID $MQTT_HOST $GENERATED_ENERGY