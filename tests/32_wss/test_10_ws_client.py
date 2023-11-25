import logging
import pytest

from ravvi_poker.engine.events import Command, Message
from ravvi_poker.ws.client import WS_Client

from helpers.x_wss import X_WebSocket, X_WSS_ClientManager

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_ws_cleint():
    x_ws = X_WebSocket()
    x_ws._commands = [
        dict(table_id=777, cmd_type=Command.Type.JOIN, take_seat=True),
        1, 
    ]
    users=[
        dict(user_id=10, cards_open=False, cards=[11,12], hand_type='A', hand_cards=[11,12,13,14,15]),
        dict(user_id=20, cards_open=True, cards=[21,22], hand_type='B', hand_cards=[21,22,23,24,25]),
        dict(user_id=30, cards_open=False, cards=[31,32], hand_type='C', hand_cards=[31,32,33,34,35]),
    ]

    x_mgr = X_WSS_ClientManager()
    x_mgr._messages = [
        Message(id=1, msg_type=Message.Type.TABLE_INFO, table_id=777, client_id=100, table_redirect_id=777, users=users),
        Message(id=2, msg_type=Message.Type.PLAYER_CARDS, table_id=777, **users[0]),
        Message(id=3, msg_type=Message.Type.PLAYER_CARDS, table_id=777, **users[1]),
        Message(id=4, msg_type=Message.Type.PLAYER_CARDS, table_id=777, **users[2]),
        Message(id=5, msg_type=Message.Type.GAME_PLAYER_MOVE, table_id=777, user_id=30, options=[1,2,3]),
    ]

    client = WS_Client(x_mgr, x_ws, user_id=10, client_id=100)
    await client.run()

    assert len(x_ws._messages)==5
    msg = x_ws._messages[0]
    assert msg.msg_type == Message.Type.TABLE_INFO
    assert msg.users[0] == {'user_id': 10, 'cards': [11, 12], 'hand_type': 'A', 'hand_cards': [11, 12, 13, 14, 15]}
    assert msg.users[1] == {'user_id': 20, 'cards': [21, 22], 'hand_type': 'B', 'hand_cards': [21, 22, 23, 24, 25]}
    assert msg.users[2] == {'user_id': 30, 'cards': [0, 0]}

    msg = x_ws._messages[1]
    assert msg.msg_type == Message.Type.PLAYER_CARDS
    assert msg.user_id == 10
    assert msg.cards == [11, 12]
    assert msg.hand_type and msg.hand_cards

    msg = x_ws._messages[2]
    assert msg.msg_type == Message.Type.PLAYER_CARDS
    assert msg.user_id == 20
    assert msg.cards == [21, 22]
    assert msg.hand_type and msg.hand_cards

    msg = x_ws._messages[3]
    assert msg.msg_type == Message.Type.PLAYER_CARDS
    assert msg.user_id == 30
    assert msg.cards == [0, 0]
    assert not msg.hand_type and not msg.hand_cards

    msg = x_ws._messages[4]
    assert msg.msg_type == Message.Type.GAME_PLAYER_MOVE
    assert msg.user_id == 30
    assert not msg.options

    #for cmd in x_mgr._commands:
    #    logger.info(cmd)

    #for msg in x_ws._messages:
    #    logger.info(msg)
