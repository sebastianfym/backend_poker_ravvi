from .router import router
from ..utils import SessionUUID
from ...db import DBI


@router.post("/logout")
async def v1_user_logout(session_uuid: SessionUUID):
    """Logout"""
    async with DBI() as db:
        session = await db.get_session_info(uuid=session_uuid) if session_uuid else None
        if session:
            await db.close_session(session.session_id)
            await db.close_login(session.login_id)
    return {}