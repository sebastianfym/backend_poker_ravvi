import uvicorn


def main():
    uvicorn.run("ravvi_poker_backend.api.main:app", host="127.0.0.1", port=5000, log_level="info")


if __name__ == "__main__":
    main()
