
import os
import json
import pytest

from ravvi_poker_backend.game.table import User
from ravvi_poker_backend.game.game import Game


def test_case(case_file):
    print(case_file)
    with open(case_file,'r') as f:
        data = json.load(f)
    users = data.get('users')
    deck = data.get('deck')
    moves = data.get('moves')

    users = [User(u) for u in users]
    game = Game(users)
    game.deck = list(deck)

    def do_player_move(timeout):
        if not moves:
            raise StopIteration()
        user_id, bet_name, amount = moves.pop(0)
        if game.current_player.user_id != user_id:
            raise ValueError()
        game.current_player.bet_type = Game.bet_code(bet_name)
        game.current_player.bet_amount = amount

    game.sleep = do_player_move
    game.run()


def load_game_cases():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(test_dir,'cases')
    cases = []
    for name in os.listdir(data_dir):
       if name[:5] != 'case-' or name[-5:]!='.json':
          continue
       path = os.path.join(data_dir, name)
       cases.append(path)
    cases.sort()
    return cases

def pytest_generate_tests(metafunc):
    if "case_file" in metafunc.fixturenames:
        metafunc.parametrize("case_file", load_game_cases())


if __name__=="__main__":
   pytest.main()