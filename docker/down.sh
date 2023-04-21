#!/usr/bin/env bash
DIR=`dirname "${BASH_SOURCE[0]}"`
FILE="${DIR}/docker-compose.yml"
docker compose -f ${FILE} down
