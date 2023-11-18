import logging
from typing import Mapping
from ..db import DBI
from ..logging import Logger_MixIn
from ..engine.event import Event, TABLE_ERROR
from .table_base import Table
from .table_ring import Table_RING
from .table_sng import Table_SNG
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
        self.log_info("client %s -> %s", client.client_id, client.tables)
        for table in self.tables.values():
            await table.remove_client(client)
        self.log_info("client %s removed", client.client_id)

    async def dispatch_command(self, client, command):
        self.log_debug("dispath: %s", command)
        table = self.tables.get(command.table_id, None)
        if command.type == Event.CMD_TABLE_JOIN:
            if not table:
                with DBI() as db:
                    table_row = db.get_table(command.table_id)
                if table_row:
                    self.log_info("table %s loaded", table_row.id) 
                    table = await self.add_table(table_row)
            if not table:
                event = TABLE_ERROR(command.table_id, error_id=404, message='Table not found')
                await client.send_event(event)
        if not table:
            return
        await table.handle_command(client, command)


    async def add_table(self, table_row):
        try:
            kwargs = table_row._asdict()
            props = kwargs.pop("game_settings", {}) or {}
            kwargs.update(props)
            if table_row.table_type == "RING_GAME":
                table = Table_RING(**kwargs)
            elif table_row.table_type == "SNG":
                table = Table_SNG(**kwargs)
            self.tables[table.table_id] = table
        
            await table.start()

            n_bots = table_row.n_bots or 0
            self.logger.info('Manager: table#%s:%s n_bots:%s', table.table_id, table.table_type, n_bots)
            for bot, _ in zip(self.bots, range(n_bots)):
                self.logger.info('Manager: table#%s: add bot#%s', table.table_id, bot.user_id)
                await bot.join_table(table.table_id)

        except Exception as ex:
            self.log_exception("add_table %s: %s", table_row, ex)
            return None

        return table
    
    async def start(self):
        for i in range(1, 4):
            bot = Bot(self, i)
            self.bots.append(bot)
            await bot.start()

        # get list of tables
        with DBI() as db:
            tables = db.get_active_tables()
            self.log_info("loaded %s tables", len(tables))

        for row in tables:
            await self.add_table(row)

        self.logger.info('Manager: started: %s tables, %s bots', len(self.tables), len(self.bots))

    async def stop(self):
        for bot in self.bots:
            await bot.stop()
        for table in self.tables.values():
            await table.stop()
        self.tables = {}
        self.bots = []
        self.logger.info('Manager: stopped')
