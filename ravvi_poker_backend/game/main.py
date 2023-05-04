from .table import Table, User
from .game import Game

if __name__=='__main__':
    t = Table(9)
    t.seats[1] = User(111)
    t.seats[3] = User(333)
    t.seats[4] = User(444)
    t.seats[7] = User(777)

    print(Game.rounds())
    for i in range(1):
        users = t.get_players()
        game = Game(users)
        game.begin()
        step = 0
        while game.round!=game.ROUND_SHOWDOWN:
            step += 1
            print("=", step, "=")
            p = game.current_player
            game.onPlayerBet(p.user_id, "CALL", None)
