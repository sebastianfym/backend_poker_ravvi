#!/usr/bin/env bash
docker exec ravvi_py bash -lc "ravvi_poker_db drop develop"
docker exec ravvi_py bash -lc "ravvi_poker_db create develop"
docker exec ravvi_py bash -lc "ravvi_poker_db deploy develop"
