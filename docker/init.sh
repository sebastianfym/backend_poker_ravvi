#!/usr/bin/env bash
docker exec ravvi_py bash -lc "pip3 install --upgrade pip"
docker exec ravvi_py bash -lc "pip3 install -e code[tests]"
docker exec ravvi_py bash -lc "ravvi_poker_db drop develop"
docker exec ravvi_py bash -lc "ravvi_poker_db create develop"
docker exec ravvi_py bash -lc "ravvi_poker_db deploy develop"
