import logging
import json
import asyncio
from typing import Mapping

from ..db.adbi import DBI
from ..db.listener import DBI_Listener
from .table import Table, Table_Regular


class Engine_Manager(DBI_Listener):

    logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.tables : Mapping[int, Table] = None
        self.channels = {
            'event_cmd' : self.on_event_cmd,
            'user_client_closed' : self.on_user_client_closed
        }

    async def run(self):
        try:
            self.tables = {}
            await super().run()
        except asyncio.CancelledError:
            pass
        finally:
            for x in self.tables.values():
                x.task_stop = True
            for x in self.tables.values():
                await x.stop()
            self.tables = None

    async def on_listen(self, db: DBI):
        self.log_info("load tables")
        rows = await db.get_open_tables()
        for r in rows:
            await self.handle_table_row(r)
        self.log_info("tables ready")

    async def on_event_cmd(self, db: DBI, *, event_id=None, event_type=None, table_id=None, client_id=None):
        self.log_debug("on_event_cmd: %s %s %s", event_id, table_id, event_type)
        if not id or not table_id:
            return
        table = self.tables.get(table_id, None)
        if not table:
            self.log_warning('table %s not found', table_id)
            return
        event = await db.get_event(id)
        if not event:
            self.log_warning('event %s not found', id)
            return
        client = await db.get_client_info(client_id)
        if not client:
            self.log_warning('client %s not found', client_id)
            return
        await table.handle_cmd(db, client.user_id, event.client_id, event.type, event.props or {})

    async def on_user_client_closed(self, db: DBI, *, client_id):
        self.log_debug("on_user_client_closed: %s %s %s", client_id)
        client = await db.get_client_info(client_id)
        if not client:
            self.log_warning('client %s not found', client_id)
            return
        user_id = client.user_id
        for table in self.tables.values():
            if client.user_id not in table.users:
                continue
            table.handle_client_close(db, user_id, client_id)

    def table_kwargs_from_row(self, row):
        kwargs = row._asdict()
        props = kwargs.pop("game_settings", {}) or {}
        kwargs.update(props)
        return kwargs
        
    def table_factory(self, *, id, table_type, **kwargs):
        if table_type=='RING_GAME':
            return Table_Regular(id=id, **kwargs)
        #if table_type=='SNG':
        #    return Table_SNG(id=id, table_type=table_type, **kwargs)

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
