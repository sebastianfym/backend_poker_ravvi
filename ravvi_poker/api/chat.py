from typing import Optional

import aiohttp
import jwt
from fastapi import APIRouter, Request, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel, model_validator, field_validator

from ..db import DBI
from ..engine.jwt import jwt_get
from ..engine.tables import TablesManager

from .utils import SessionUUID, get_session_and_user

router = APIRouter(prefix="/chats", tags=["chats"])


class ChatMessage(BaseModel):
    id: int | None = None
    table_id: int | None = None
    sender_id: int | None = None
    text: str | None = None


@router.get("/{table_id}/messages", status_code=200, summary="List messages for current table")
async def v1_get_all_messages_for_table(table_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        messages = await db.get_table_msgs(table_id)

    returned_msgs_list = [ChatMessage(id=msg.id, table_id=msg.table_id, sender_id=msg.sender_id, text=msg.text) for msg
                          in messages]
    return returned_msgs_list


@router.post("/{table_id}/messages/", status_code=200, summary="Send message to the current table")
async def v1_send_message_to_table(table_id: int, message_text: ChatMessage, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        table = await db.get_table(table_id)
        if table is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        else:
            message = await db.write_message_from_chat_in_db(table_id, user.id, message_text)

            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f'http://localhost:8000/chat/ws/{table_id}') as ws: #Todo заменить путь к ws
                    await ws.send_str(str(message_text))

            return ChatMessage(id=message.id, table_id=message.table_id, sender_id=message.sender_id, text=message.text)

