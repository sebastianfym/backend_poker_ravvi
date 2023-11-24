from typing import List
import pytest
from ravvi_poker.engine.poker.player import User, PlayerRole

from ravvi_poker.game.user import User
from ravvi_poker.engine.poker.bet import Bet
from ravvi_poker.game.poker import PokerBase, Round, Player, Event

class PokerBaseTest(PokerBase):
    def __init__(self, table, game_id, users: List[User], deck=None) -> None:
        super().__init__(table, game_id, users)
        self._deck = deck
        self._event = None

    async def broadcast(self, event: Event):
        self._event = event

@pytest.mark.asyncio
async def test_42_poker_4_players():
    users = [User(x, f"u{x}", 1000) for x in [111, 222, 333, 444]]
    
    # game with random deck
    game = PokerBaseTest(None, 1, users)
    assert game.table is None
    assert game.game_id == 1
    assert game.round is None
    assert len(game.players) == len(users)
    for p, u in zip(game.players, users):
        assert p.user is u
    assert game.deck is None
    assert game.cards is None
    assert game.banks is None

    game.setup_players_roles()
    assert game.dealer_id == users[0].id

    p = game.players[0]
    assert p.user_id == 111
    assert p.role == PlayerRole.DEALER
    p = game.players[1]
    assert p.user_id == 222
    assert p.role == PlayerRole.SMALL_BLIND
    p = game.players[2]
    assert p.user_id == 333
    assert p.role == PlayerRole.BIG_BLIND
    p = game.players[3]
    assert p.user_id == 444
    assert p.role == PlayerRole.DEFAULT

    game.players_rotate()
    assert game.current_player.user_id == 222
    game.players_rotate()
    assert game.current_player.user_id == 333
    game.players_rotate()
    assert game.current_player.user_id == 444
    game.players_rotate()
    assert game.current_player.user_id == 111

    game.players_to_role(PlayerRole.BIG_BLIND)
    assert game.current_player.user_id == 333

    game.players_to_role(PlayerRole.SMALL_BLIND)
    assert game.current_player.user_id == 222

    game.players_to_role(PlayerRole.DEALER)
    assert game.current_player.user_id == 111

    game.setup_cards()
    assert game.deck
    assert game.cards == []
    for p in game.players:
        assert p.cards == []
        assert p.cards_open == False


if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    import asyncio
    asyncio.run(test_42_poker_4_players())