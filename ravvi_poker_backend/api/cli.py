#import logging
import uvicorn


def main():
    uvicorn.run("ravvi_poker_backend.api.main:app", host="0.0.0.0", port=5000, log_level="info")


if __name__ == "__main__":
    main()
