import pytest

from ravvi_poker_backend.game.user import User
from ravvi_poker_backend.game.bet import Bet
from ravvi_poker_backend.game.game import Game, Round, Player


@pytest.mark.asyncio
async def test_30_game_acceptance():
    users = [User(x, f"u{x}", 1000) for x in [111, 333, 444]]
    deck  = [1,2,3,4,5,6,7,8,9,10,11,12,13,14]
    game = Game(users, deck=deck)

    assert len(game.players) == 3
    assert game.players[0].user_id == 111
    assert game.players[1].user_id == 333
    assert game.players[2].user_id == 444
    assert game.dealer_id == 111
    assert not game.round
    assert not game.active_count
    assert not game.bet_level
    assert not game.bets_all_same
    assert not game.bank
    assert game.cards is None

    # begin
    await game.on_begin()

    assert game.round == Round.PREFLOP
    assert game.bank == 0
    assert game.active_count == 3

    p = game.players[0]
    assert p.role == Player.ROLE_DEALER
    assert p.bet_type is None
    assert p.bet_amount == 0
    assert p.cards == [1,2]
    assert p.cards_open == False

    p = game.players[1]
    assert p.role == Player.ROLE_SMALL_BLIND
    assert p.bet_type == Bet.SMALL_BLIND
    assert p.bet_amount == 1
    assert p.cards == [3,4]
    assert p.cards_open == False

    p = game.players[2]
    assert p.role == Player.ROLE_BIG_BLIND
    assert p.bet_type == Bet.BIG_BLIND
    assert p.bet_amount == 2
    assert p.cards == [5,6]
    assert p.cards_open == False

    async def move_1():
        game.handle_bet(111, Bet.CALL, None)
        assert game.current_player.bet_amount == 2

    game.wait_for_player = move_1
    await game.run_step()

    async def move_2():
        game.handle_bet(333, Bet.CALL, None)
        assert game.current_player.bet_amount == 2

    game.wait_for_player = move_2
    await game.run_step()

    async def move_3():
        game.handle_bet(444, Bet.CHECK, None)
        assert game.current_player.bet_amount == 2

    game.wait_for_player = move_3
    await game.run_step()

    assert game.round == Round.FLOP

    async def move_4():
        game.handle_bet(333, Bet.CHECK, None)

    game.wait_for_player = move_4
    await game.run_step()

    async def move_5():
        game.handle_bet(444, Bet.CHECK, None)

    game.wait_for_player = move_5
    await game.run_step()

    async def move_6():
        game.handle_bet(111, Bet.CHECK, None)

    game.wait_for_player = move_6
    await game.run_step()

    assert game.round == Round.TERN