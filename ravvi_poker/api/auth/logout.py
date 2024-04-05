from .router import router
from ..utils import SessionUUID
from ...db import DBI
from fastapi import Request


@router.post("/logout")
async def v1_user_logout(session_uuid: SessionUUID, request: Request):
    """Logout"""
    async with DBI() as db:
        session = await db.get_session_info(uuid=session_uuid) if session_uuid else None
        if session:
            try:
                client_host = request.client.host
            except AttributeError:
                client_host = "127.0.0.1"
            await db.close_session(session.session_id, host=client_host)
            await db.close_login(session.login_id, host=client_host)
    return {}