import logging

from ravvi_poker.engine.user import User
from ravvi_poker.engine.cards import Card
from ravvi_poker.engine.events import Message, Command
from ravvi_poker.engine.poker.bet import Bet

logger = logging.getLogger(__name__)

def x_users(_users):
    users = []
    for x in _users:
        balance = x.pop('balance')
        u = User(**x)
        u.balance = balance
        u.clients.add(u.id)
        users.append(u)
    return users

class X_CaseMixIn:
    SLEEP_ROUND_BEGIN = 0
    SLEEP_ROUND_END = 0
    SLEEP_SHOWDOWN_CARDS = 0
    SLEEP_GAME_END = 0

    def __init__(self, table, game_id, _users, _deck, _moves, **kwargs) -> None:
        super().__init__(table, game_id, x_users(_users), **kwargs)
        self._deck = [Card(x).code for x in _deck]
        self._check_steps = list(enumerate(_moves, 1))
        logger.info("%s %s", self.table, self.game_id)

    def setup_cards(self):
        super().setup_cards()
        self.deck = self._deck

    async def emit_msg(self, db, msg: Message):
        self.x_check_msg(msg)
        await super().emit_msg(db, msg)

    def x_check_msg(self, msg: Message):
        self.log.debug("%s", msg)
        assert self._check_steps
        step_num, step = self._check_steps.pop(0)
        step_msg = f"msg {step_num}"
        pre, check_event, post = None, None, None
        if isinstance(step, dict):
            check_event = step
        else:
            raise ValueError('invalid check entry', step_num)

        msg_type = check_event.pop('type')
        check_event['msg_type'] = Message.Type.decode(msg_type)
        #check_event = Message(**check_event)
        for k, ev in check_event.items():
            rv = msg.get(k, None)
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
        cmd_type = cmd.pop('type')
        cmd_type = Command.Type.decode(cmd_type)
        cmd = Command(table_id=-1, client_id=-1, cmd_type=cmd_type, **cmd)
        assert cmd.cmd_type == Command.Type.BET, step_msg
        assert cmd.user_id == self.current_player.user_id, step_msg
        async with self.DBI() as db:
            await self.handle_cmd(self, db, cmd.user_id, cmd.client_id, cmd.cmd_type, cmd.props)

def create_game_case(base):
# creating class dynamically 
    name = f"X_{base.__name__}"
    cls = type(name, (X_CaseMixIn, base), {})
    return cls

import os
import json

def load_game_cases(test_file):
    test_dir = os.path.dirname(os.path.abspath(test_file))    
    data_dir = os.path.join(test_dir,'cases')
    cases = []
    for name in os.listdir(data_dir):
       if name[:5] != 'case-' or name[-5:]!='.json':
          continue
       cases.append(name)
    cases.sort()
    cases = [(name, load_case_data(data_dir, name)) for name in cases]
    return cases

def load_case_data(data_dir, case_file):
    path = os.path.join(data_dir, case_file)
    with open(path,'r') as f:
        lines = [l for l in f.readlines() if l[:2]!='//']
        case_data = json.loads(''.join(lines))
    case_data['_users'] = case_data.pop('users',None)
    case_data['_deck'] = case_data.pop('deck',None)
    case_data['_moves'] = case_data.pop('moves',None)
    return case_data
