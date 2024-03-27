from starlette.status import HTTP_200_OK

from .router import *
from ..utils import SessionUUID, get_session_and_user
from ...db import DBI
from ...engine.info import rewards_distribution


@router.get("/rewards_distribution", status_code=HTTP_200_OK, summary="Get rewards distribution structure")
async def v1_get_payment_structure(session_uuid: SessionUUID):
    """
    Получаем структуру распределения выигрыша в турнирах.
    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)

    return rewards_distribution