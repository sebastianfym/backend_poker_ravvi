
import os
import json
import pytest
from ravvi_poker.game.cards import Card
from ravvi_poker.game.event import Event
from ravvi_poker.game.user import User
from ravvi_poker.game.bet import Bet

from ravvi_poker.game.poker_plo import Poker_PLO_5

class GameCase(Poker_PLO_5):

    SLEEP_ROUND_BEGIN = 0
    SLEEP_ROUND_END = 0
    SLEEP_SHOWDOWN_CARDS = 0
    SLEEP_GAME_END = 0

    def __init__(self, game_id, *, users, deck, moves, **kwargs) -> None:
        super().__init__(None, game_id, [User(**user) for user in users])
        self._deck = [Card(x).code for x in deck]
        self._check_steps = list(enumerate(moves, 1))

    def setup_cards(self):
        super().setup_cards()
        self.deck = self._deck

    async def broadcast(self, event: Event):
        self.log_debug("%s", event)
        assert self._check_steps
        step_num, step = self._check_steps.pop(0)
        step_msg = f"broadcast {step_num}"
        pre, check_event, post = None, None, None
        if isinstance(step, dict):
            check_event = step
        else:
            raise ValueError('invalid check entry', step_num)

        check_event['type'] = getattr(Event, check_event['type'])
        check_event = Event(**check_event)
        for k, ev in check_event.items():
            rv = event.get(k, None)
            if k=='cards' and ev:
                ev = [Card(x).code for x in ev]
            elif k=='options' and ev:
                ev = [Bet.decode(x) for x in ev]
                rv = [Bet.decode(x) for x in rv]
            elif k=='bet':
                ev = Bet.decode(ev)
                rv = Bet.decode(rv)
            assert ev == rv, f"{step_msg} - {k}"


    async def wait_for_player_bet(self):
        assert self._check_steps
        step_num, step = self._check_steps.pop(0)
        step_msg = f"wait_for_player_bet {step_num}"
        pre, cmd, post = None, None, None
        if step is None:
            cmd = None
        elif isinstance(step, dict):
            cmd = step
        else:
            raise ValueError('invalid check entry', step_num)
        if not cmd:
            # do nothing
            return

        cmd['type'] = getattr(Event, cmd['type'])
        cmd = Event(**cmd)
        assert cmd.type == Event.CMD_PLAYER_BET, step_msg
        assert cmd.user_id == self.current_player.user_id, step_msg
        bet_code = getattr(Bet, cmd.bet)
        self.handle_bet(cmd.user_id, Bet(bet_code), cmd.amount)


test_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(test_dir,'cases')

@pytest.mark.asyncio
async def test_case(case_file):
    print(case_file)
    path = os.path.join(data_dir, case_file)
    with open(path,'r') as f:
        lines = [l for l in f.readlines() if l[:2]!='//']
        case_data = json.loads(''.join(lines))

    game = GameCase(1, **case_data)
    await game.run()
    assert not game._check_steps

def load_game_cases():
    cases = []
    for name in os.listdir(data_dir):
       if name[:5] != 'case-' or name[-5:]!='.json':
          continue
       cases.append(name)
    cases.sort()
    return cases

def pytest_generate_tests(metafunc):
    if "case_file" in metafunc.fixturenames:
        metafunc.parametrize("case_file", load_game_cases())


if __name__=="__main__":
    import logging
    import sys
    case_file = sys.argv[1]
    import asyncio
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_case(case_file))