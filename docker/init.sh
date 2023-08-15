#!/usr/bin/env bash
docker exec ravvi_py bash -lc "pip3 install --upgrade pip"
docker exec ravvi_py bash -lc "python3 code/build_version.py"
docker exec ravvi_py bash -lc "pip3 install -e code[tests] --no-build-isolation"
docker exec ravvi_py bash -lc "ravvi_poker_db drop develop"
docker exec ravvi_py bash -lc "ravvi_poker_db create develop"
docker exec ravvi_py bash -lc "ravvi_poker_db deploy develop"
