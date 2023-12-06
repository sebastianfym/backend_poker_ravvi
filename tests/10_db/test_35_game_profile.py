import pytest
import pytest_asyncio

from ravvi_poker.db.dbi import DBI


class X_Player:
    def __init__(self, user, balance) -> None:
        self.user = user
        self.balance = balance

    @property
    def id(self):
        return self.user.id
    
    @property
    def user_id(self):
        return self.user.id

#@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_game_create(table, users_10):
    users = users_10[:9]

    async with DBI() as db:
        game = await db.create_game(table_id=table.id, game_type=table.game_type, game_subtype=table.game_subtype, props=None, players=None)
        assert game.props is not None

    async with DBI() as db:
        game, game_players = await db.get_game_and_players(game.id)
        assert game
        assert game.props is not None
        assert not game_players

    props = dict(blind_value=1)
    players = [X_Player(u, 10+i*10) for i, u in enumerate(users)]
    players.sort(key=lambda x: x.user_id)

    assert players
    async with DBI() as db:
        game = await db.create_game(table_id=table.id, game_type=table.game_type, game_subtype=table.game_subtype, props=props, players=players)
        assert game.props

    async with DBI() as db:
        game, game_players = await db.get_game_and_players(game.id)
        assert game
        assert game_players
        assert len(game_players) == len(players)
        game_players.sort(key=lambda x: x.user_id)
        for p, gp in zip(players, game_players):
            assert p.user_id == gp.user_id
            assert p.balance == gp.balance_begin

    for p in players:
        p.balance += 10

    async with DBI() as db:
        game = await db.close_game(game.id, players)

    async with DBI() as db:
        game, game_players = await db.get_game_and_players(game.id)
        assert game
        assert game_players
        assert len(game_players) == len(players)
        game_players.sort(key=lambda x: x.user_id)
        for p, gp in zip(players, game_players):
            assert p.user_id == gp.user_id
            assert p.balance == gp.balance_end
            assert gp.balance_end == gp.balance_begin+10

