import logging
import asyncio
import random

from ..engine.clients.base import ClientQueue, Message, Command, ClientsManager
from ..engine.poker.bet import Bet

logger = logging.getLogger(__name__)

class DummyBot(ClientQueue):
    
    def __init__(self, manager: ClientsManager, client_id, user_id) -> None:
        super().__init__(manager, client_id, user_id)
        self.log.logger = logger

    async def join_table(self, table_id):
        cmd = Command(client_id=None, table_id=table_id, cmd_type=Command.Type.JOIN, take_seat=True)
        await self.send_cmd(cmd)

    def bet_weight(self, x):
        if x in [Bet.CHECK, Bet.CALL]:
            return 10
        if x == Bet.RAISE:
            return 5
        if x == Bet.FOLD:
            return 1
        return 0

    async def on_msg(self, msg: Message):
        msg_type = Message.Type(msg.msg_type)
        self.log.debug("msg#%s %s %s", msg.id, msg_type, msg.props)
        if msg_type != Message.Type.GAME_PLAYER_MOVE:
            return
        if not msg.options:
            return
        self.log.warning("table_id:%s options:%s raise:[%s - %s]", msg.table_id, msg.options, msg.raise_min, msg.raise_max)
        # select option
        sleep_seconds = random.randint(0,1)
        self.log.warning("thinking %s sec ...", sleep_seconds)
        await asyncio.sleep(sleep_seconds)
        options = [x for x in msg.options]
        weights = [self.bet_weight(x) for x in options]
        choice = random.choices(options, weights)[0]
        amount = msg.raise_min if choice==Bet.RAISE else None
        self.log.warning("choice %s %s", choice, amount)
        cmd = Command(client_id=None, table_id=msg.table_id, cmd_type=Command.Type.BET, bet = choice, amount = amount)
        await self.send_cmd(cmd)
