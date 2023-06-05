import pytest
import json
from ravvi_poker.game.event import Event
from ravvi_poker.game.table import Table
from ravvi_poker.game.client import Client


class TableMock(Table):

    def __init__(self, table_id, n_seats=9):
        super().__init__(table_id, n_seats)
        self._test_events = []

    async def broadcast(self, event: Event):
        self._test_events.append(event)

class ClientMock(Client):
    def __init__(self, manager, user_id, *, logger_name=None) -> None:
        super().__init__(manager, user_id, logger_name=logger_name)
        self._test_events = []

    async def send_event(self, event):
        self._test_events.append(event)

    def comsume_events(self):
        self._test_events = []

def test_01_table_players():
    table = TableMock(1, 9)
    table.seats[1] = table.get_user(111, connected=1)
    table.seats[3] = table.get_user(333, connected=1)
    table.seats[4] = table.get_user(444, connected=1)
    table.seats[7] = table.get_user(777, connected=1)

    players = table.get_players(min_size=3)
    assert len(players) == 4
    assert players[0].id == 111
    assert players[1].id == 333
    assert players[2].id == 444
    assert players[3].id == 777

    # user 444 left table
    table.seats[4] = None

    players = table.get_players(min_size=3)
    assert len(players) == 3
    assert players[0].id == 333
    assert players[1].id == 777
    assert players[2].id == 111

    # user 555 joined
    table.seats[5] = table.get_user(555, connected=1)

    players = table.get_players(min_size=3)
    assert len(players) == 4
    assert players[0].id == 555
    assert players[1].id == 777
    assert players[2].id == 111
    assert players[3].id == 333

    # user 222 joined
    table.seats[2] = table.get_user(222, connected=1)

    players = table.get_players(min_size=3)
    assert len(players) == 5
    assert players[0].id == 777
    assert players[1].id == 111
    assert players[2].id == 222
    assert players[3].id == 333
    assert players[4].id == 555


def check_TABLE_INFO(client):
    assert len(client._test_events)==1
    event = client._test_events[0]
    assert event.type == Event.TABLE_INFO
    json.dumps(event)
    client.comsume_events()


@pytest.mark.asyncio
async def test_01_table_clients():
    table = TableMock(1, 9)
    # no seats occupied
    assert all(x is None for x in table.seats)

    # new client connected
    client_0 = ClientMock(None, 111)

    # requested to join as viewer
    await table.add_client(client_0, take_seat=False)
    # no seats occupied
    assert all(x is None for x in table.seats)
    assert table.clients[0] == client_0
    assert client_0.tables == set()
    assert not table._test_events

    check_TABLE_INFO(client_0)

    # new client connected
    client_1 = ClientMock(None, 222)

    # requested to join as viewer
    await table.add_client(client_1, take_seat=False)
    assert all(x is None for x in table.seats)
    assert table.clients[1] == client_1
    assert client_1.tables == set()
    assert not table._test_events

    check_TABLE_INFO(client_1)

    # requested to join as player
    await table.add_client(client_1, take_seat=True)
    user = table.seats[0]
    assert user.id == 222
    assert user.connected == 1
    assert table.clients[1] == client_1
    assert client_1.tables == set([1])

    assert len(table._test_events)==1
    event = table._test_events[0]
    assert event.type == Event.PLAYER_ENTER
    json.dumps(event)

    client_1.comsume_events()    

    # new client connected
    client_2 = ClientMock(None, 222)

    # requested to join as player
    table._test_events = []
    await table.add_client(client_2, take_seat=True)
    user = table.seats[0]
    assert user.id == 222
    assert user.connected == 2
    assert table.clients[2] == client_2
    assert client_1.tables == set([1])
    assert not table._test_events

    check_TABLE_INFO(client_2)

    # exit from server
    table._test_events = []
    await table.remove_client(client_1)
    user = table.seats[0]
    assert user.id == 222
    assert user.connected == 1
    assert len(table.clients) == 2
    assert client_1.tables == set()
    assert not table._test_events

    # exit from server
    table._test_events = []
    await table.remove_client(client_2)
    user = table.seats[0]
    assert user.id == 222
    assert user.connected == 0
    assert len(table.clients) == 1
    assert client_1.tables == set()
    assert not table._test_events
