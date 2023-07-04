from ravvi_poker.game.player import User, Player
from ravvi_poker.game.game import get_banks, Bet

def test_30_multibank():
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

    banks = get_banks(players)

    #for i, (amount, group) in enumerate(banks, 1):
    #    print(i, amount, [(p.user.id, p.bet_total) for p in group])

    assert len(banks) == 3
    amount, group = banks[0]
    assert amount == 900
    amount, group = banks[1]
    assert amount == 200
    amount, group = banks[2]
    assert amount == 100

if __name__=="__main__":
    test_30_multibank()
