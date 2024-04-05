import asyncio
import requests
from urllib.parse import urlencode
import websockets
import json
from ravvi_poker.engine.event import Event, CMD_PLAYER_BET, CMD_TABLE_JOIN

API_URL = "localhost:5000"
WS_URL = "localhost:5001"

def register_guest():
    response = requests.post(f"http://{API_URL}/api/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username

async def hello():
    access_token, username = register_guest()
    params = urlencode(dict(access_token=access_token))
    uri = f"ws://{WS_URL}/api/v1/ws?access_token={access_token}"

    async with websockets.connect(uri) as ws:

        cmd = CMD_TABLE_JOIN(table_id=11, take_seat=True)
        await ws.send(json.dumps(cmd))

        while True:
            msg = await ws.recv()
            kwargs = json.loads(msg)
            event = Event(**kwargs)
            print(event)
            if event.type == Event.GAME_PLAYER_MOVE and event.options:
                print("Enter bet code:")
                choice = int(input())
                cmd = CMD_PLAYER_BET(table_id=event.table_id, bet=choice)
                await ws.send(json.dumps(cmd))


if __name__ == "__main__":
    asyncio.run(hello())
