import logging
import json
import asyncio
from typing import Mapping

from .event import Event
from .table import Table
from ..db.adbi import DBI, Notify
from ..db.listener import DBI_Listener
from ..game.table_ring import Table_RING
from ..game.table_sng import Table_SNG


class Engine_Manager(DBI_Listener):

    logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.tables : Mapping[int, Table]= None
        self.channels = dict(
            poker_event_cmd = self.on_poker_event_cmd
        )

    async def run(self):
        try:
            self.tables = {}
            await super().run()
        finally:
            for x in self.tables.values():
                await x.stop()
            self.tables = None

    async def on_listen_begin(self, db: DBI):
        rows = await db.get_open_tables()
        for r in rows:
            await self.handle_table_row(r)

    async def on_poker_event_cmd(self, db: DBI, *, id, type, table_id, client_id):
        if not id or table_id:
            return
        table = self.tables.get(table_id, None)
        if not table:
            return
        event_row = db.get_event(id)
        if not event_row:
            return
        await table.handle_cmd(db, event_row)

    def table_kwargs_from_row(self, row):
        kwargs = row._asdict()
        props = kwargs.pop("game_settings", {}) or {}
        kwargs.update(props)
        return kwargs
        
    def table_factory(self, *, id, table_type, **kwargs):
        if table_type=='RING_GAME':
            return Table_RING(id=id, table_type=table_type, **kwargs)
        if table_type=='SNG':
            return Table_SNG(id=id, table_type=table_type, **kwargs)

    async def handle_table_row(self, table_row):
        self.log_info("handle_table_row: %s", table_row)
        try:
            kwargs = self.table_kwargs_from_row(table_row)
            table = self.table_factory(**kwargs)
            self.tables[table.table_id] = table
            # run table task
            await table.start()

        except Exception as ex:
            self.log_exception("add_table %s: %s", table_row, ex)
