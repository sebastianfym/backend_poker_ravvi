from ravvi_poker.engine.poker.player import User, Player, Bet
from ravvi_poker.engine.poker.multibank import get_banks

def test_multibank_1():
    users = [User(x, f"u{x}", 1000) for x in [111, 222, 333, 444, 555, 666, 777, 888, 999]]
    players = [Player(u) for u in users]
    players[0].bet_total = 100
    players[0].bet_type = Bet.ALLIN
    players[1].bet_total = 100
    players[1].bet_type = Bet.ALLIN
    players[2].bet_total = 100
    players[2].bet_type = Bet.FOLD
    players[3].bet_total = 100
    players[3].bet_type = Bet.ALLIN
    players[4].bet_total = 300
    players[4].bet_type = Bet.ALLIN
    players[5].bet_total = 100
    players[5].bet_type = Bet.ALLIN
    players[6].bet_total = 100
    players[6].bet_type = Bet.ALLIN
    players[7].bet_total = 100
    players[7].bet_type = Bet.ALLIN
    players[8].bet_total = 200
    players[8].bet_type = Bet.ALLIN

    banks, total = get_banks(players)

 #   for i, (amount, group) in enumerate(banks, 1):
 #       print(i, amount, [(p.user.id, p.bet_total) for p in group])

    assert total == 1200

    assert len(banks) == 3
    amount, group = banks[0]
    assert amount == 900
    amount, group = banks[1]
    assert amount == 200
    amount, group = banks[2]
    assert amount == 100

def test_multibank_2():
    users = [User(x, f"u{x}", 1000) for x in [111, 222, 333, 444, 555, 666, 777, 888, 999]]
    players = [Player(u) for u in users]
    players[0].bet_total = 100
    players[0].bet_type = Bet.ALLIN
    players[1].bet_total = 200
    players[1].bet_type = Bet.ALLIN
    players[2].bet_total = 300
    players[2].bet_type = Bet.FOLD
    players[3].bet_total = 400
    players[3].bet_type = Bet.FOLD
    players[4].bet_total = 500
    players[4].bet_type = Bet.FOLD
    players[5].bet_total = 600
    players[5].bet_type = Bet.FOLD
    players[6].bet_total = 700
    players[6].bet_type = Bet.ALLIN
    players[7].bet_total = 800
    players[7].bet_type = Bet.ALLIN
    players[8].bet_total = 900
    players[8].bet_type = Bet.ALLIN

    banks, total = get_banks(players)

#    for i, (amount, group) in enumerate(banks, 1):
#        print(i, amount, [(p.user.id, p.bet_total) for p in group])

    assert total == 4500

    assert len(banks) == 5
    amount, group = banks[0]
    assert amount == 900
    amount, group = banks[1]
    assert amount == 800
    amount, group = banks[2]
    assert amount == 2500
    amount, group = banks[3]
    assert amount == 200
    amount, group = banks[4]
    assert amount == 100
