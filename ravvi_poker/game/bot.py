import logging
import asyncio
import random
from .client import Client
from .bet import Bet
from .event import Event, CMD_TABLE_JOIN


class Bot(Client):

    def __init__(self, manager, user_id) -> None:
        super().__init__(manager, user_id, logger_name=__name__+f".{user_id}")
        self.task : asyncio.Task = None

    async def start(self):
        self.task = asyncio.create_task(self.run())

    async def stop(self):
        if not self.task:
            return
        if not self.task.done():
            self.task.cancel()
        await self.task
        self.task = None

    async def run(self):
        self.log_info("begin")
        try:
            await self.process_queue()
        except asyncio.CancelledError:
            pass
        self.log_info("end")

    async def join_table(self, table_id):
        cmd = CMD_TABLE_JOIN(table_id=table_id, take_seat=True)
        await self.dispatch_command(cmd)

    def bet_weight(self, x):
        if x in [Bet.CHECK, Bet.CALL]:
            return 10
        if x == Bet.RAISE:
            return 5
        if x == Bet.FOLD:
            return 1
        return 0

    async def handle_event(self, event: Event):
        table_id = event.get('table_id', None)
        event_id = id(event)
        if event.type != Event.GAME_PLAYER_MOVE:
            return
        if not event.options:
            return
        self.log_debug("table_id:%s options:%s raise:[%s - %s]", 
                          event.table_id, event.options, event.raise_min, event.raise_max
                          )
        # select option
        sleep_seconds = random.randint(3,7)
        self.log_debug("thinking %s sec ...", sleep_seconds)
        await asyncio.sleep(sleep_seconds)
        options = [x for x in event.options]
        weights = [self.bet_weight(x) for x in options]
        choice = random.choices(options, weights)[0]
        amount = event.raise_min if choice==Bet.RAISE else None
        self.log_debug("choice %s %s", choice, amount)
        #
        command = Event(
            type = Event.CMD_PLAYER_BET,
            table_id = table_id,
            bet = choice,
            amount = amount
        )
        await self.dispatch_command(command)
        
