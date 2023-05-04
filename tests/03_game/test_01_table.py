from ravvi_poker_backend.game.table import Table, User
from ravvi_poker_backend.game.game import Game, Player


def test_01_table():
    t = Table(9)
    t.seats[1] = User(111)
    t.seats[3] = User(333)
    t.seats[4] = User(444)
    t.seats[7] = User(777)

    players = t.get_players(min_size=3)
    assert len(players) == 4
    assert players[0].user_id == 111
    assert players[1].user_id == 333
    assert players[2].user_id == 444
    assert players[3].user_id == 777

    # user 444 left table
    t.seats[4] = None

    players = t.get_players(min_size=3)
    assert len(players) == 3
    assert players[0].user_id == 333
    assert players[1].user_id == 777
    assert players[2].user_id == 111

    # user 555 joined
    t.seats[5] = User(555)

    players = t.get_players(min_size=3)
    assert len(players) == 4
    assert players[0].user_id == 555
    assert players[1].user_id == 777
    assert players[2].user_id == 111
    assert players[3].user_id == 333

    # user 222 joined
    t.seats[2] = User(222)

    players = t.get_players(min_size=3)
    assert len(players) == 5
    assert players[0].user_id == 777
    assert players[1].user_id == 111
    assert players[2].user_id == 222
    assert players[3].user_id == 333
    assert players[4].user_id == 555
