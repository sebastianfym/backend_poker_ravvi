from typing import List

from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from .router import *
from ..tables.types import TableParams, TableProfile
from ..utils import SessionUUID, get_session_and_user
from ...db import DBI


@router.get("/{table_id}/result", status_code=200, summary="Get table (SNG/MTT) result")
async def v1_get_table_result(table_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        table = await db.get_table(table_id)
        if not table:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        if table.table_type not in ('SNG', 'MTT'):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        rows = await db.get_table_result(table_id)
        rows.sort(key=lambda x: x.balance_end or x.balance_begin or 0, reverse=True)
        result = []
        for i, r in enumerate(rows, start=1):
            x = dict(
                user_id=r.user_id,
                username=r.username,
                image_id=r.image_id,
                reward=r.balance_end,
                rank=i
            )
            result.append(x)
    return dict(result=result)