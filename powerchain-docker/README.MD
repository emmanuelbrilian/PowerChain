To run the projects infrastructure for the first time:
`docker compose up -d mongo mosquitto ganache`

To run the projects infrastructure:
`docker compose start mongo mosquitto ganache`

To build the server & peer project:
`docker compose stop server peer1 peer2 [PEER_N]`
`docker compose rm server peer1 peer2 [PEER_N]`
`docker compose build server peer1 peer2 [PEER_N]`

To run the projects for the first time:
`docker compose up -d server peer1 peer2 peer3 [PEER_N]`
`docker compose up -d server peer1 peer2 peer3 peer4 peer5 peer6 peer7 peer8 peer9 peer10`

To run the projects:
`docker compose start server peer1 peer2 peer3 peer4 peer5 peer6 peer7 peer8 peer9 peer10`
