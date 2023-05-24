import logging
from typing import Mapping
from ..db import DBI
from ..logging import Logger_MixIn
from .event import Event, TABLE_ERROR
from .table import Table
from .bot import Bot


class Manager(Logger_MixIn):

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
        self.log_debug("dispath: %s", command)
        table = self.tables.get(command.table_id, None)
        if not table:
            if command.type == Event.CMD_TABLE_JOIN:
                event = TABLE_ERROR(command.table_id, error_id=404, message='Table not found')
                client.send(event)
            return
        await table.handle_command(client, command)

    def add_table(self, table_id):
        table = Table(table_id, 9)
        self.tables[table_id] = table
        return table

    async def start(self):
        # get list of tables
        with DBI() as db:
            tables = db.get_active_tables()

        for row in tables:
            table = self.add_table(row.id)
            await table.start()

        for i in range(1, 4):
            bot = Bot(self, i)
            self.bots.append(bot)
            await bot.start()
        self.logger.info('Manager: started: %s tables, %s bots', len(self.tables), len(self.bots))

    async def stop(self):
        for bot in self.bots:
            await bot.stop()
        self.bots = []

        for table in self.tables.values():
            await table.stop()
        self.tables = {}
        self.logger.info('Manager: stopped')
