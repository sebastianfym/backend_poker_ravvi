from starlette.status import HTTP_404_NOT_FOUND, HTTP_200_OK
from fastapi import Request, HTTPException
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user, check_club_name
from .router import router
from .types import *


@router.get("/{club_id}/relation_clubs", status_code=HTTP_200_OK,
            summary="Returns all relationships with other clubs for the club with the ID")
async def v1_get_relation_clubs(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        # relations = await db.get_club_relations(club_id=club_id) #Todo такой функции в dbi.py нету, название примерное
        relations_clubs = []  # Todo после того, как у нас появятся связи в бд вернуть строку выше, которая будет возвращать список состоящий из союзных клубов
        return [ClubProfile(
            id=club.id,
            name=club.name,
            description=club.description,
            image_id=club.image_id
        ) for club in relations_clubs]


@router.get("/{union_id}/relation_union", status_code=HTTP_200_OK, summary="Get a union by id")
async def v1_get_relation_union(union_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        try:
            union = await db.get_unions(union_id)  # Todo такой функции в dbi.py нету, название примерное
        except AttributeError:
            union = None
        if not union:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Union not found")

        return UnionProfile(name=union.name)


@router.get("/relations/unions", status_code=HTTP_200_OK, summary='Get all unions')
async def v1_get_all_unions(session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        try:
            unions = await db.get_unions()  # Todo такой функции в dbi.py нету, название примерное
        except AttributeError:
            unions = None
        if not unions:
            return []
        return [UnionProfile(id=union.id, name=union.name) for union in unions]