from ravvi_poker.game.player import User, Player, PlayerRole

def test_21_player():
    u = User(77, 'u77', None, 1000)
    
    p = Player(u)
    assert p.user == u
    assert p.user_id == 77
    assert p.balance == 1000
    assert p.role == Player.ROLE_DEFAULT
    assert p.cards is None
    assert p.cards_open == False
    assert p.bet_type is None
    assert p.bet_amount == 0
    assert p.bet_delta == 0
    assert p.bet_total == 0
    assert p.bet_max == 1000
    assert p.in_the_game
    assert p.has_bet_opions

def test_21_player_role():
    role = PlayerRole.DEFAULT
    assert PlayerRole.DEALER not in role
    assert PlayerRole.SMALL_BLIND not in role
    assert PlayerRole.BIG_BLIND not in role

    role = PlayerRole.DEALER
    assert PlayerRole.DEALER in role
    assert PlayerRole.SMALL_BLIND not in role
    assert PlayerRole.BIG_BLIND not in role

    role = PlayerRole.SMALL_BLIND
    assert PlayerRole.DEALER not in role
    assert PlayerRole.SMALL_BLIND in role
    assert PlayerRole.BIG_BLIND not in role

    role = PlayerRole.BIG_BLIND
    assert PlayerRole.DEALER not in role
    assert PlayerRole.SMALL_BLIND not in role
    assert PlayerRole.BIG_BLIND in role

    role = PlayerRole.DEALER | PlayerRole.SMALL_BLIND
    assert PlayerRole.DEALER in role
    assert PlayerRole.SMALL_BLIND in role
    assert PlayerRole.BIG_BLIND not in role

if __name__=="__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_21_player_role()