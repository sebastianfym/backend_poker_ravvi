import asyncio
import websockets


async def hello():

    uri = "ws://localhost:15000/v1/ws_test"

    async with websockets.connect(uri) as ws:
        while True:
            msg = await ws.recv()
            print(msg)


if __name__ == "__main__":

    asyncio.run(hello())
