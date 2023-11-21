To run this peer project, make sure infrastructure & server are running:
See powerchain-server README.MD

And run this peer:
`python app.py [PEER_ID] [MQTT_HOST]`
PEER_ID = ObjectId in mongodb collection User.

Example
`python app.py ssg3467dahjq localhost`

Or simply
`python app.py ssg3467dahjq` with default as above.


To test publishing:
`python app.py [PEER_ID] [MQTT_HOST] [TARGET_PEER_ID]`
