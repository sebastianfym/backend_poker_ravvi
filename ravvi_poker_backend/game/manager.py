import logging
from typing import Mapping
from .table import Table
from .bot import Bot

class Manager:

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        self.tables: Mapping[int,Table] = {}
        self.bots = []

    async def _add_client(self, client):
        table = self.tables.get(1, None)
        if table:
            await table.add_client(client, True)

    async def remove_client(self, client):
        for table in self.tables.values():
            await table.remove_client(client)

    async def dispatch_command(self, client, command):
        command.update(user_id = client.user_id)
        self.logger.debug("dispatch -> %s", command)
        table_id = command.table_id
        if not table_id:
            return
        table = self.tables.get(table_id, None)
        if not table:
            return
        await table.handle_command(command)

    def add_table(self, table_id):
        table = Table(9)
        table.table_id = table_id
        self.tables[table_id] = table
        return table

    async def start(self):
        table = self.add_table(1)
        await table.start()

        for i in range(1, 4):
            bot = Bot(self, i)
            await bot.start()
            await self._add_client(bot)
            self.bots.append(bot)
        print('Manager: started', len(self.tables), len(self.bots))

    async def stop(self):
        for bot in self.bots:
            await bot.stop()
        self.bots = []

        for table in self.tables.values():
            await table.stop()
        self.tables = {}
        print('Manager: stopped')