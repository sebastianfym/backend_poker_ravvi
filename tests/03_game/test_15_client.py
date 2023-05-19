import pytest

from ravvi_poker_backend.game.client import Client
from ravvi_poker_backend.game.event import Event, PLAYER_CARDS, GAME_PLAYER_MOVE


def test_1_PLAYER_CARDS():

    client = Client(None, 777)

    # same user - visible cards
    event = PLAYER_CARDS(user_id=777, cards=[1,2], cards_open=False)
    result = client.process_event(event)

    assert result.type == Event.PLAYER_CARDS
    assert result.user_id == 777
    assert result.cards == [1,2]

    # other user - closed cards - hide
    event = PLAYER_CARDS(user_id=111, cards=[3,4], cards_open=False)
    result = client.process_event(event)

    assert result.type == Event.PLAYER_CARDS
    assert result.user_id == 111
    assert result.cards == [0,0]
    assert event.cards == [3,4]

    # other user - open cards - show
    event = PLAYER_CARDS(user_id=222, cards=[5,6], cards_open=True)
    result = client.process_event(event)

    assert result.type == Event.PLAYER_CARDS
    assert result.user_id == 222
    assert result.cards == [5,6]


def test_2_GAME_PLAYER_MOVE():

    client = Client(None, 777)
    
    # same user
    event = GAME_PLAYER_MOVE(user_id=777, options=[1,2,3,4])
    result = client.process_event(event)

    assert result.type == Event.GAME_PLAYER_MOVE
    assert result.user_id == 777
    assert result.options == [1,2,3,4]

    # other user
    event = GAME_PLAYER_MOVE(user_id=111, options=[1,2,3,4])
    result = client.process_event(event)

    assert result.type == Event.GAME_PLAYER_MOVE
    assert result.user_id == 111
    assert result.options is None
    assert event.options == [1,2,3,4]
