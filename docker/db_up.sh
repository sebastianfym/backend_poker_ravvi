#!/usr/bin/env bash
DIR=`dirname "${BASH_SOURCE[0]}"`
FILE="${DIR}/docker-compose.yml"
docker compose -f ${FILE} up -d postgres
sleep 3
ravvi_poker_db create develop
ravvi_poker_db deploy develop
