# from fastapi import APIRouter
# from fastapi.exceptions import HTTPException
# from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
# from pydantic import BaseModel
#
# from .tables import TableProfile
# from ..db import DBI
# from .utils import SessionUUID, get_session_and_user
#
# router = APIRouter(prefix="/lobby", tags=["lobby"])
#
#
# @router.get("/entry_tables", status_code=200, summary="Get game entry points")
# async def v1_get_entry_tables(session_uuid: SessionUUID):
#     async with DBI() as db:
#         _, user = await get_session_and_user(db, session_uuid)
#         tables = await db.get_lobby_entry_tables()
#     return list([
#         TableProfile(
#             id=table.id,
#             club_id=table.club_id,
#             table_name=table.table_name,
#             table_type=table.table_type,
#             table_seats=table.table_seats,
#             game_type=table.game_type,
#             game_subtype=table.game_subtype,
#             **table.props
#         ) for table in tables
#     ])
