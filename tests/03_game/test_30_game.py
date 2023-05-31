import pytest

from ravvi_poker.game.user import User
from ravvi_poker.game.bet import Bet
from ravvi_poker.game.game import Game, Round, Player

def prepare_player_bet(game: Game, user_id, bet, amount, check_amount=None):
    async def _handler():
        assert game.current_player.user_id == user_id
        game.handle_bet(user_id, bet, amount)
        if check_amount is not None:
            assert game.current_player.bet_amount == check_amount
    game.wait_for_player_bet = _handler

@pytest.mark.asyncio
async def test_30_game_acceptance():
    users = [User(x, f"u{x}", 1000) for x in [111, 333, 444]]
    # game with random deck
    game = Game(None, 1, users)

    # game with predefined deck
    deck  = [1,2,3,4,5,6,7,8,9,10,11,12,13,14]
    game = Game(None, 1, users, deck=deck)

    assert len(game.players) == 3
    assert game.players[0].user_id == 111
    assert game.players[1].user_id == 333
    assert game.players[2].user_id == 444
    assert game.dealer_id == 111
    assert not game.round
    assert not game.count_in_the_game
    assert not game.bet_level
    assert not game.bets_all_same
    assert not game.bank
    assert game.cards is None

    # begin
    await game.on_begin()

    assert game.round == Round.PREFLOP
    assert game.bank == 0
    assert game.count_in_the_game == 3

    p = game.players[0]
    assert p.role == Player.ROLE_DEALER
    assert p.bet_type is None
    assert p.bet_amount == 0
    assert p.cards == [5,6]
    assert p.cards_open == False

    p = game.players[1]
    assert p.role == Player.ROLE_SMALL_BLIND
    assert p.bet_type == Bet.SMALL_BLIND
    assert p.bet_amount == 1
    assert p.cards == [1,2]
    assert p.cards_open == False

    p = game.players[2]
    assert p.role == Player.ROLE_BIG_BLIND
    assert p.bet_type == Bet.BIG_BLIND
    assert p.bet_amount == 2
    assert p.cards == [3,4]
    assert p.cards_open == False

    prepare_player_bet(game, 111, Bet.CALL, None, 2)
    await game.run_step()
    assert game.count_in_the_game == 3
    assert game.count_has_options == 3
    assert game.current_player.user_id == 333

    prepare_player_bet(game, 333, Bet.CALL, None, 2)
    await game.run_step()
    assert game.count_in_the_game == 3
    assert game.count_has_options == 3
    assert game.current_player.user_id == 444

    prepare_player_bet(game, 444, Bet.CHECK, None, 2)
    await game.run_step()
    assert game.count_in_the_game == 3
    assert game.count_has_options == 3
    assert game.bet_level == 0
    assert game.bets_all_same

    assert game.current_player.user_id == 333
    assert game.round == Round.FLOP
    assert game.bank == 6
    assert game.count_in_the_game == 3

    prepare_player_bet(game, 333, Bet.CHECK, None, 0)
    await game.run_step()

    prepare_player_bet(game, 444, Bet.CHECK, None, 0)
    await game.run_step()

    prepare_player_bet(game, 111, Bet.CHECK, None, 0)
    await game.run_step()

    assert game.round == Round.TERN
    assert game.bank == 6
    assert game.count_in_the_game == 3

    prepare_player_bet(game, 333, Bet.CHECK, None, 0)
    await game.run_step()

    prepare_player_bet(game, 444, Bet.RAISE, 4, 4)
    await game.run_step()

    prepare_player_bet(game, 111, Bet.CALL, None, 4)
    await game.run_step()

    prepare_player_bet(game, 333, Bet.CALL, None, 4)
    await game.run_step()

#    prepare_player_bet(game, 444, Bet.CHECK, None, 4)
#    await game.run_step()

#    prepare_player_bet(game, 111, Bet.CHECK, None, 4)
#    await game.run_step()

    assert game.round == Round.RIVER
    assert game.bank == 6+12
    assert game.count_in_the_game == 3

    prepare_player_bet(game, 333, Bet.CHECK, None, 0)
    await game.run_step()

    prepare_player_bet(game, 444, Bet.FOLD, None, 0)
    await game.run_step()

    prepare_player_bet(game, 111, Bet.CHECK, None, 0)
    await game.run_step()

    assert game.round == Round.SHOWDOWN
    assert game.bank == 18
    assert game.count_in_the_game == 2

    await game.on_end()

if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    import asyncio
    asyncio.run(test_30_game_acceptance())