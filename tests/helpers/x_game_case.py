import asyncio
import logging
from decimal import Decimal
from typing import Any

from ravvi_poker.engine.user import User
from ravvi_poker.engine.cards import Card
from ravvi_poker.engine.events import Message, Command
from ravvi_poker.engine.poker.bet import Bet
from ravvi_poker.engine.poker.hands import HandType, LowHandType

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


class X_Deck:
    def __init__(self, cards):
        self.cards = cards

    def get_next(self):
        return self.cards.pop(0)


class X_CaseMixIn:
    SLEEP_ROUND_BEGIN = 0
    SLEEP_ROUND_END = 0
    SLEEP_ROUND_RESULT = 0
    SLEEP_SHOWDOWN_CARDS = 0
    SLEEP_GAME_END = 0

    def __init__(self, table, _users, _deck, _moves, **kwargs) -> None:
        super().__init__(table, x_users(_users), **kwargs)
        self.game_id = 1
        self._deck = [Card(x).code for x in _deck]
        self._check_steps = list(enumerate(_moves, 1))

    def setup_boards(self):
        super().setup_boards()
        self.deck = X_Deck(self._deck)

    async def emit_msg(self, db, msg: Message):
        print(f"Ожидаю {msg}")
        await self.x_check_msg(msg)
        await super().emit_msg(db, msg)

    async def x_check_msg(self, msg: Message):
        assert self._check_steps
        step_num, step = self._check_steps.pop(0)
        step_msg = f"msg {step_num}"
        if isinstance(step, dict):
            expected = step
        else:
            raise ValueError('invalid check entry', step_num)

        msg_type = expected.pop('type')
        task = None
        # если мы видим что игра предлагает карты для сброса, то поищем действия сброса инициированные пользователем
        if msg_type == "GAME_PROPOSED_CARD_DROP":
            # поищем команду drop для этого пользователя
            for step_num, step in self._check_steps:
                if "CMD_PLAYER_DROP_CARD" in step["type"] and step["user_id"] == msg["props"]["user_id"]:
                    print(f"find cmd to drop card: card - {step['card']}, user - {step['user_id']}")
                    self._check_steps.remove((step_num, step))
                    asyncio.create_task(self.translate_drop_card_msg_to_cmd(step))
                    break
        elif msg_type == "CMD_PLAYER_SHOW_CARD":
            task = asyncio.create_task(self.translate_show_cards_msg_to_cmd(step))
            # берем следующее сообщение
            step_num, step = self._check_steps.pop(0)
            expected = step
            msg_type = expected.pop('type')

        expected['msg_type'] = Message.Type.decode(msg_type)
        cmp = [(k, v, getattr(msg, k, None)) for k, v in expected.items()]
        # self.log.info("%s msg: %s", step_num, msg.props)
        # self.log.info("%s expected: %s", step_num, cmp)
        for k, ev in expected.items():
            rv = getattr(msg, k, None)
            if k == 'cards':
                # TODO посмотреть зачем тут list
                if isinstance(ev[0], str):
                    ev = [Card(x).code for x in ev]
                elif isinstance(ev[0], list):
                    ev = [[Card(x).code for x in ev_item] for ev_item in ev]
            elif k == 'boards':
                ev = [{"board_type": board["board_type"], "cards": [Card(x).code for x in board["cards"]]}
                      for board in ev]
                rv = [{"board_type": board["board_type"], "cards": [Card(x).code for x in board["cards"]]}
                      for board in rv]
            elif k == 'options' and ev:
                ev = [Bet.decode(x) for x in ev]
                rv = [Bet.decode(x) for x in rv]
            elif k == 'bet':
                ev = Bet.decode(ev)
                rv = Bet.decode(rv)
            elif k == 'hands':
                if len(ev) == 1:
                    # REGULAR games
                    ev[0]["hand_cards"] = [Card(x).code for x in ev[0]["hand_cards"]]
                    ev[0]["hand_type"] = HandType.decode(ev[0]["hand_type"])
                    rv[0]["hand_type"] = HandType.decode(rv[0]["hand_type"])
                else:
                    for i in range(len(ev)):
                        # Low hand in Hi-Low
                        if ev[i]["hand_belong"] == "low":
                            if ev[i]["hand_type"] is not None:
                                ev[i]["hand_cards"] = [Card(x).code for x in ev[i]["hand_cards"]]
                                ev[i]["hand_type"] = LowHandType.decode(ev[i]["hand_type"])
                                rv[i]["hand_type"] = LowHandType.decode(rv[i]["hand_type"])
                            else:
                                ev[i]["hand_cards"] = []
                                ev[i]["hand_type"] = None
                                rv[i]["hand_type"] = None
                        # DoubleBoard|2-3
                        else:
                            ev[i]["hand_cards"] = [Card(x).code for x in ev[i]["hand_cards"]]
                            ev[i]["hand_type"] = HandType.decode(ev[i]["hand_type"])
                            rv[i]["hand_type"] = HandType.decode(rv[i]["hand_type"])

            assert ev == rv, f"{step_msg} - {k}: {ev} / {rv}"

        if task:
            await task

    def is_low_hand(self, hand):
        return set(hand) <= set("2345678A") if hand is not None else True

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
        cmd_type = Command.Type.BET if cmd_type == 'CMD_PLAYER_BET' else Command.Type.decode(cmd_type)
        assert cmd_type == Command.Type.BET, step_msg
        cmd['bet'] = Bet.decode(cmd['bet'])
        cmd = Command(table_id=-1, client_id=-1, cmd_type=cmd_type, **cmd)
        self.log.debug("cmd %s", cmd)
        assert cmd.user_id == self.current_player.user_id, step_msg
        async with self.DBI() as db:
            await self.handle_cmd(db, cmd.user_id, cmd.client_id, cmd.cmd_type, cmd.props)

    async def translate_drop_card_msg_to_cmd(self, msg):
        cmd_type = Command.Type.DROP_CARD
        cmd = {"card": msg["card"], "user_id": msg["user_id"]}
        cmd = Command(table_id=-1, client_id=-1, cmd_type=cmd_type, **cmd)
        self.log.debug("cmd %s", cmd)
        async with self.DBI() as db:
            await self.handle_cmd(db, cmd.user_id, cmd.client_id, cmd.cmd_type, cmd.props)

    async def translate_show_cards_msg_to_cmd(self, msg):
        cmd_type = Command.Type.SHOW_CARDS
        cmd = {"cards": msg["cards"], "user_id": msg["user_id"]}
        cmd = Command(table_id=-1, client_id=-1, cmd_type=cmd_type, **cmd)
        self.log.debug("cmd %s", cmd)
        async with self.DBI() as db:
            await self.handle_cmd(db, cmd.user_id, cmd.client_id, cmd.cmd_type, cmd.props)


def create_game_case(base):
    # creating class dynamically
    name = f"X_{base.__name__}"
    cls = type(name, (X_CaseMixIn, base), {})
    return cls


import os
import json


def load_game_cases(test_file):
    test_dir = os.path.dirname(os.path.abspath(test_file))
    data_dir = os.path.join(test_dir, 'cases')
    cases = []
    for name in os.listdir(data_dir):
        if name[:5] != 'case-' or name[-5:] != '.json':
            continue
        cases.append(name)
    cases.sort()
    cases = [(name, load_case_data(data_dir, name)) for name in cases]
    return cases


def load_case_data(data_dir, case_file):
    path = os.path.join(data_dir, case_file)
    with open(path, 'r') as f:
        lines = [l for l in f.readlines() if l[:2] != '//']
        case_data = json.loads(''.join(lines))
    case_data['_users'] = case_data.pop('users', None)
    case_data['_deck'] = case_data.pop('deck', None)
    case_data['_moves'] = case_data.pop('moves', None)
    # приведем все float к Decimal
    cast_float_to_decimal(case_data)

    return case_data


def cast_float_to_decimal(data: Any):
    if isinstance(data, list):
        for num, v in enumerate(data):
            if isinstance(v, float):
                data[num] = Decimal(v).quantize(Decimal(".01"))
            else:
                cast_float_to_decimal(data[num])
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, float):
                data[k] = Decimal(v).quantize(Decimal(".01"))
            else:
                cast_float_to_decimal(data[k])
