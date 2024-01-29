import pytest

from ravvi_poker.engine.user import User
from ravvi_poker.engine.poker.bet import Bet
from ravvi_poker.engine.poker.base import PokerBase


@pytest.mark.asyncio
async def test_31_bet_timeout():

    users = [User(x, f"u{x}", None) for x in [111, 333, 444]]
    for u in users:
        u.clients.add(u.id)
        u.balance = 1000
    
    # game with random deck
    game = PokerBase(None, users, blind_small=1, blind_big=2, bet_timeout=0.1)
    game.banks =[]
    game.bank_total = 0
    game.setup_players_roles()
    game.setup_cards()
    #await game.broadcast_GAME_BEGIN()
    await game.run_PREFLOP()

    p111, p333, p444 = sorted(game.players, key=lambda x: x.user_id)
    assert p111.user_id == 111
    assert p111.bet_type == Bet.FOLD
    assert p333.user_id == 333
    assert p111.bet_type == Bet.FOLD
    assert p444.user_id == 444
    assert p444.bet_type is None

