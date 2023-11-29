import logging
import json
import asyncio
from typing import Mapping

from ..db import DBI
from ..db.listener import DBI_Listener
from .table import Table, Table_RG, Table_SNG

logger = logging.getLogger(__name__)

class Engine_Manager(DBI_Listener):

    def __init__(self):
        super().__init__()
        self.log = logger
        self.tables: Mapping[int, Table] = None
        self.channels = {
            "table_profile_created": self.on_table_profile_created, 
            "table_cmd": self.on_table_cmd, 
            "user_client_closed": self.on_user_client_closed
        }

    async def run(self):
        try:
            self.tables = {}
            await super().run()
        except asyncio.CancelledError:
            pass
        finally:
            self.log.info("shutdown tables ...")
            for x in self.tables.values():
                x.task_stop = True
            for x in self.tables.values():
                await x.stop()
            self.log.info("shutdown tables done")
            self.tables = None

    async def on_listen(self, db: DBI):
        self.log.info("load tables")
        rows = await db.get_open_tables()
        for r in rows:
            await self.handle_table_row(r)
        self.log.info("tables ready")

    async def on_table_profile_created(self, db: DBI, *, table_id):
        self.log.debug("on_table_profile_created: %s ", table_id)
        row = await db.get_table(table_id)
        if not row:
            self.log.warning("table_id=%s not found", table_id)
        await self.handle_table_row(row)

    async def on_table_cmd(self, db: DBI, *, cmd_id, table_id):
        self.log.info("on_table_cmd: %s: %s", table_id, cmd_id)
        table = self.tables.get(table_id, None)
        if not table:
            self.log.warning("table %s not found", table_id)
            return
        cmd = await db.get_table_cmd(cmd_id)
        if not cmd:
            self.log.warning("table_cmd %s not found", cmd_id)
            return
        client = await db.get_client_info(cmd.client_id)
        if not client:
            self.log.warning("client %s not found", cmd.client_id)
            return
        try:
            await table.handle_cmd(db, cmd_id=cmd_id, client_id=client.client_id, user_id=client.user_id, cmd_type=cmd.cmd_type, props=(cmd.props or {}))
        except Exception as e:
            self.log.exception("%s", e)
        finally:
            await db.set_table_cmd_processed(cmd_id)


    async def on_user_client_closed(self, db: DBI, *, client_id):
        self.log.info("on_user_client_closed: %s ", client_id)
        client = await db.get_client_info(client_id)
        if not client:
            self.log.warning("client %s not found", client_id)
            return
        user_id = client.user_id
        for table in self.tables.values():
            if client.user_id not in table.users:
                continue
            await table.handle_client_close(db, user_id=user_id, client_id=client_id)

    def table_factory(self, row):
        kwargs = row._asdict()
        if row.table_type == "RG":
            return Table_RG(**kwargs)
        elif row.table_type=='SNG':
            return Table_SNG(**kwargs)
        self.log.error("table %s unknown table_type=%s", row.id, row.table_type)

    async def handle_table_row(self, row):
        self.log.info("handle_table_row: %s", row.id)
        if row.id in self.tables:
            self.log.warning("%s already in tables", row.id)
            return
        try:
            table = self.table_factory(row)
            if not table:
                return
            self.tables[table.table_id] = table
            # run table task
            await table.start()
        except Exception as ex:
            self.log.exception("add_table %s: %s", row, ex)
