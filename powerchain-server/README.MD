To run this server, make sure infrastructure are running.
`cd powerchain-docker`
`docker compose start mongo ganache msquitto`

Or to bring it up at first time
`docker compose up -d mongo ganache msquitto`


Then run the server locally
`python app.py [mongo_host] [ethereum_host] [mqtt_host] [mqtt_client_id]`

Example
`python app.py localhost localhost localhost powerchain-server-1`


Or simply
`python app.py` with default as above.
