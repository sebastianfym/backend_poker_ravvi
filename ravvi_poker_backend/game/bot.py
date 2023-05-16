import logging
import asyncio
import random
from ..events import Events
from .client import Client
from .game import Game
from .event import Event


class Bot(Client):

    logger = logging.getLogger(__name__)

    def __init__(self, manager, user_id) -> None:
        super().__init__(manager, user_id)
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
        self.logger.info(" %s: begin", self.user_id)
        try:
            await self.process_game_events()
        except asyncio.CancelledError:
            pass
        self.logger.info(" %s: end", self.user_id)

    async def handle_game_event(self, event: Event):
        table_id = event.get('table_id', None)
        if event.type != Event.GAME_PLAYER_MOVE:
            return
        if not event.options:
            return
        self.logger.debug(" %s: table_id:%s options:%s raise:%s-%s", 
                          self.user_id, event.table_id, 
                          event.options, event.raise_min, event.raise_max
                          )
        # select option
        sleep_seconds = random.randint(5,10)
        self.logger.debug(" %s: thinking %s sec ...", self.user_id, sleep_seconds)        
        await asyncio.sleep(sleep_seconds)
        choice = random.choice(event.options)
        self.logger.debug(" %s: choice %s", self.user_id, Game.bet_name(choice))
        #
        command = Event(
            type = Event.CMD_PLAYER_BET,
            table_id = table_id,
            bet = choice,
            amount = event.raise_min if choice==Game.BET_RAISE else None
        )
        await self.manager.dispatch_command(self, command)
        
