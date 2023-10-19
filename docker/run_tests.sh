#!/usr/bin/env bash
docker exec ravvi_py bash -lc "cd code/tests; coverage run -m pytest -v"
#docker exec ravvi_py bash -lc "cd code/tests; coverage report"
