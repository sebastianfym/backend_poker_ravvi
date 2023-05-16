import asyncio
import requests
from urllib.parse import urlencode
import websockets
import json
from ravvi_poker_backend.game.event import Event, PLAYER_BET

API_URL = "localhost:5000"

def register_guest():
    response = requests.post(f"http://{API_URL}/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username

async def hello():
    access_token, username = register_guest()
    params = urlencode(dict(access_token=access_token))
    uri = f"ws://{API_URL}/v1/ws_test?access_token={access_token}"

    async with websockets.connect(uri) as ws:
        while True:
            msg = await ws.recv()
            kwargs = json.loads(msg)
            event = Event(**kwargs)
            print(event)
            if event.type == Event.GAME_PLAYER_MOVE and event.options:
                print("Enter bet code:")
                choice = int(input())
                command = Event(
                    type=Event.CMD_PLAYER_BET, 
                    table_id=event.table_id, 
                    user_id=event.user_id,
                    bet=choice
                )
                await ws.send(json.dumps(command))


if __name__ == "__main__":

    asyncio.run(hello())
