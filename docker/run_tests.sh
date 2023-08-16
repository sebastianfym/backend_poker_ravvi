#!/usr/bin/env bash
docker exec ravvi_py bash -lc "cd code/tests; pytest -v"
