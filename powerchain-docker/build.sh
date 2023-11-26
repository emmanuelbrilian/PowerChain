#!/bin/sh

docker compose build

docker compose stop server peer1 peer2 peer3 peer4 peer5 peer6 peer7 peer8 peer9 peer10
docker compose rm server peer1 peer2 peer3 peer4 peer5 peer6 peer7 peer8 peer9 peer10
docker compose up -d server peer1 peer2 peer3 peer4 peer5 peer6 peer7 peer8 peer9 peer10
