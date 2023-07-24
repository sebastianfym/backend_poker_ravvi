import datetime
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

router = APIRouter(prefix="/debug", tags=["debug"])

class DebugMessage(BaseModel):
    id: int
    game_id: int | None = None
    table_id: int | None = None
    message: str | None = None
    created_ts: datetime.datetime


class DebugMessageCreate(BaseModel):
    game_id: int
    table_id: int
    message: str | None = None


@router.post("", summary="Send debug message")
async def v1_send_debug_message(params: DebugMessageCreate, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        game = dbi.get_game(params.game_id)
        if not game:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Game not found")
        table = dbi.get_table(params.table_id)
        if not table:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        debug_message = dbi.create_debug_message(user.id, params.game_id, params.table_id, params.message)

    return DebugMessage(
        id=debug_message.id,
        game_id=debug_message.game_id,
        table_id=debug_message.table_id,
        message=debug_message.debug_message,
        created_ts=debug_message.created_ts,
    )


@router.get("", summary="Get debug messages")
async def v1_get_debug_messages(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        debug_messages = dbi.get_debug_messages(user.id)

    return list([
        DebugMessage(
            id=message.id,
            game_id=message.game_id,
            table_id=message.table_id,
            message=message.debug_message,
            created_ts=message.created_ts,
        ) for message in debug_messages
    ])
