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
                    table = self.add_table(table_row)
                    if table:
                        await table.start()
            if not table:
                event = TABLE_ERROR(command.table_id, error_id=404, message='Table not found')
                client.send(event)
        if not table:
            return
        await table.handle_command(client, command)

    def add_table(self, table_row):
        try:
            game_type = table_row.game_type
            n_seats = 9
            if not game_type:
                game_type = 'PLO' if table_row.id==2 else 'NLH'
            if game_type=='PLO':
                n_seats = min(n_seats, 6)
            table = Table(table_row.id, game_type=game_type, n_seats=n_seats)
            self.tables[table.id] = table
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
            table = self.add_table(row)
            if not table:
                continue
            await table.start()
            if row.club_id:
                continue
            for bot in self.bots:
                await bot.join_table(table.table_id)

        self.logger.info('Manager: started: %s tables, %s bots', len(self.tables), len(self.bots))

    async def stop(self):
        for bot in self.bots:
            await bot.stop()
        for table in self.tables.values():
            await table.stop()
        self.tables = {}
        self.bots = []
        self.logger.info('Manager: stopped')
