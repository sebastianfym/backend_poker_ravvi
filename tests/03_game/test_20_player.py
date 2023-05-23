from ravvi_poker.game.player import User, Player

def test_21_player():
    u = User(77, 'u77', 1000)
    
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
    assert p.bet_max == 1000
    assert p.has_bet_opions
