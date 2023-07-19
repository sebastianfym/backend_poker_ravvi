from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

router = APIRouter(prefix="/clubs", tags=["clubs"])


class ClubProps(BaseModel):
    name: str
    description: str | None = None
    image_id: int | None = None


class ClubUpdateProps(BaseModel):
    name: str | None = None
    description: str | None = None
    image_id: int | None = None


class ClubProfile(BaseModel):
    id: int
    name: str
    description: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool


@router.post("", status_code=201, summary="Create new club")
async def v1_create_club(params: ClubProps, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        image = dbi.get_user_images(user.id, id=params.image_id) if params.image_id else None
        if params.image_id is not None and not image:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Image not found")
        club = dbi.create_club(founder_id=user.id, **params.model_dump())

    return ClubProfile(
        id=club.id, 
        name=club.name, 
        description=club.description,
        image_id=club.image_id,
        user_role="OWNER",
        user_approved=True
    )


@router.get("", summary="List clubs for current user")
async def v1_list_clubs(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        clubs = dbi.get_clubs_for_user(user_id=user.id)

    return [
        ClubProfile(
            id=club.id, 
            name=club.name, 
            description=club.description,
            image_id=club.image_id,
            user_role=club.user_role,
            user_approved=club.approved_ts is not None
        ) for club in clubs
    ]


@router.get("/{club_id}", summary="Get club by id")
async def v1_get_club(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_member = dbi.get_club_member(club_id, user.id)

    return ClubProfile(
        id=club.id,
        name=club.name,
        description=club.description,
        image_id=club.image_id,
        user_role=club_member.user_role if club_member else None,
        user_approved=club_member.approved_ts is not None if club_member else None
    )


@router.patch("/{club_id}", summary="Update club")
async def v1_update_club(club_id: int, params: ClubUpdateProps, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_member = dbi.get_club_member(club_id, user.id)        
        if not club_member or club_member.user_role != "OWNER":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        club = dbi.update_club(club_id, **params.model_dump(exclude_unset=True))

    return ClubProfile(
        id=club.id, 
        name=club.name,
        description=club.description,
        image_id=club.image_id,
        user_role=club_member.user_role,
        user_approved=club_member.approved_ts is not None
    )


@router.delete("/{club_id}", status_code=204, summary="Delete club")
async def v1_delete_club(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_member = dbi.get_club_member(club_id, user.id)
        if not club_member or club_member.user_role != "OWNER":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        dbi.delete_club(club.id)

    return {}


@router.get("/{club_id}/members", summary="Get club memebrs")
async def v1_club_join_request(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        response = []
        for row in dbi.get_club_members(club_id=club.id):
            response.append(dict(
                id = row.id,
                username = row.username,
                user_role = row.user_role,
                user_approved = row.approved_ts is not None
            ))
    return response


@router.post("/{club_id}/members", summary="Submit join request")
async def v1_club_join_request(club_id: int, session_uuid: RequireSessionUUID):
    user_role='PLAYER'
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_member = dbi.create_join_club_request(club_id=club.id, user_id=user.id, user_role=user_role)
    
    return ClubProfile(
        id=club.id, 
        name = club.name, description=club.description,
        user_role = club_member.user_role if club_member else None,
        user_approved = club_member.approved_ts is not None if club_member else None
    )
