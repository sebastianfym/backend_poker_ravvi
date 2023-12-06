import pytest
from ravvi_poker.engine.poker.base import PokerBase, User, PlayerRole


@pytest.mark.asyncio
async def test_41_poker_base_2_players():
    users = [User(x, f"u{x}", None) for x in [111, 222]]
    
    game = PokerBase(None, users, blind_small=1)
    assert game.table is None
    assert game.game_id is None
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
    assert p.role == PlayerRole.DEALER|PlayerRole.SMALL_BLIND
    p = game.players[1]
    assert p.user_id == 222
    assert p.role == PlayerRole.BIG_BLIND

    game.players_rotate()
    assert game.current_player.user_id == 222
    game.players_rotate()
    assert game.current_player.user_id == 111

    game.players_to_role(PlayerRole.SMALL_BLIND)
    assert game.current_player.user_id == 111

    game.players_to_role(PlayerRole.BIG_BLIND)
    assert game.current_player.user_id == 222

    game.players_to_role(PlayerRole.SMALL_BLIND)
    assert game.current_player.user_id == 111

    game.players_to_role(PlayerRole.DEALER)
    assert game.current_player.user_id == 111

    game.setup_cards()
    assert game.deck
    assert game.cards == []
    for p in game.players:
        assert p.cards == []
        assert p.cards_open == False