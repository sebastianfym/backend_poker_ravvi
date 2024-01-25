import logging
import json
import asyncio
from typing import Mapping

from ...db import DBI
from ...db.listener import DBI_Listener
from . import Table, Table_RG, Table_SNG, TableStatus

logger = logging.getLogger(__name__)


class TablesManager(DBI_Listener):
    def __init__(self):
        super().__init__()
        self.log = logger
        self.tables_accept = True
        self.tables: Mapping[int, Table] = {}
        self.listener = DBI_Listener(log=self.log)
        self.listener.on_listen = self.on_listen
        self.listener.channels = {
            "table_profile_created": self.on_table_profile_created,
            "table_profile_status": self.on_table_profile_status,
            "table_cmd": self.on_table_cmd,
            "user_client_closed": self.on_user_client_closed,
        }

    async def start(self):
        self.tables_accept = True
        await self.listener.start()

    async def stop(self):
        self.log.info("shutdown tables ...")
        # запрещаем прием новых столов
        self.tables_accept = False
        # сигнализируем остановку для всех столов
        for x in list(self.tables.values()):
            await x.shutdown()
        # ждем завершения работы всех столов
        await self._wait_tables_closed()
        self.log.info("shutdown tables done")
        # выключаем прием оповещений
        await self.listener.stop()

    async def _wait_tables_closed(self):
        while self.tables:
            await asyncio.sleep(0.1)

    async def on_listen(self, backend_id):
        self.log.info("load tables ...")
        async with DBI() as dbi:
            tables = await dbi.get_open_tables()
        self.log.info("loaded %s tables", len(tables))
        for x in tables:
            await self.start_table(x)
        self.log.info("tables ready")

    async def on_table_profile_created(self, *, table_id):
        if not self.tables_accept:
            # прием и запуск новых столов запрещен
            return
        self.log.info("on_table_profile_created: %s ", table_id)
        async with DBI() as db:
            row = await db.get_table(table_id)
            if not row:
                self.log.warning("table_id=%s not found", table_id)
                return
            await db.lock_table_engine_id(table_id)
        await self.start_table(row)

    async def on_table_profile_status(self, *, table_id, engine_status, engine_id):
        engine_status = TableStatus(engine_status)
        self.log.info("on_table_profile_status: %s %s %s", table_id, engine_status, engine_id)
        if engine_status not in (TableStatus.STOPPED, TableStatus.CLOSED):
            return
        table = self.tables.pop(table_id, None)
        if not table:
            return
        await table.wait_done()
        async with DBI() as db:
            await db.release_table_engine_id(table_id)
        self.log.info("release table %s ", table_id)

    async def on_table_cmd(self, *, cmd_id, table_id):
        self.log.info("on_table_cmd: %s: %s", table_id, cmd_id)
        table = self.tables.get(table_id, None)
        if not table:
            return
        async with DBI() as dbi:
            cmd = await dbi.get_table_cmd(cmd_id)
            client = await dbi.get_client_info(cmd.client_id)
            if not client:
                self.log.warning("client %s not found", cmd.client_id)
                return
            try:
                await table.handle_cmd(
                    dbi,
                    cmd_id=cmd_id,
                    client_id=client.client_id,
                    user_id=client.user_id,
                    cmd_type=cmd.cmd_type,
                    props=(cmd.props or {}),
                )
            except Exception as e:
                self.log.exception("%s", e)
            finally:
                await dbi.set_table_cmd_processed(cmd_id)

    async def on_user_client_closed(self, *, client_id):
        self.log.info("on_user_client_closed: %s ", client_id)
        async with DBI() as dbi:
            client = await dbi.get_client_info(client_id)
            if not client:
                self.log.warning("client %s not found", client_id)
                return
            user_id = client.user_id
            for table in self.tables.values():
                if client.user_id not in table.users:
                    continue
                await table.handle_client_close(dbi, user_id=user_id, client_id=client_id)

    def table_factory(self, row):
        kwargs = row._asdict()
        if row.table_type == "RG":
            return Table_RG(**kwargs)
        elif row.table_type == "SNG":
            return Table_SNG(**kwargs)
        self.log.error("table %s unknown table_type=%s", row.id, row.table_type)
        

    async def start_table(self, row):
        self.log.info("handle_table_start: %s", row.id)
        if row.id in self.tables:
            self.log.warning("%s already in tables", row.id)
            return
        try:
            table = self.table_factory(row)
            # start table task
            await table.start()
            self.tables[table.table_id] = table
        except Exception as ex:
            self.log.exception("add_table %s: %s", row, ex)
