from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel

from ..db import DBI
from .utils import SessionUUID, get_session_and_user
from .tables import TableParams, TableProfile

router = APIRouter(prefix="/clubs", tags=["clubs"])


class ClubProps(BaseModel):
    name: str | None = None
    description: str | None = None
    image_id: int | None = None


class ClubProfile(BaseModel):
    id: int
    name: str
    description: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool | None = None


class ClubMemberProfile(BaseModel):
    id: int | None = None
    username: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool | None = None


@router.post("", status_code=201, summary="Create new club")
async def v1_create_club(params: ClubProps, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.create_club(user_id=user.id, name=params.name, description=params.description, image_id=params.image_id)

    return ClubProfile(
        id=club.id, 
        name=club.name, 
        description=club.description,
        image_id=club.image_id,
        user_role="OWNER",
        user_approved=True
    )


@router.get("", summary="List clubs for current user")
async def v1_list_clubs(session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        clubs = await db.get_clubs_for_user(user_id=user.id)

    return list([
        ClubProfile(
            id=club.id, 
            name=club.name, 
            description=club.description,
            image_id=club.image_id,
            user_role=club.user_role,
            user_approved=club.approved_ts is not None
        ) for club in clubs
    ])


@router.get("/{club_id}", summary="Get club by id")
async def v1_get_club(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_member = await db.find_club_member(club_id, user.id)

    return ClubProfile(
        id=club.id,
        name=club.name,
        description=club.description,
        image_id=club.image_id,
        user_role=club_member.user_role if club_member else None,
        user_approved=club_member.approved_ts is not None if club_member else None
    )


@router.patch("/{club_id}", summary="Update club")
async def v1_update_club(club_id: int, params: ClubProps, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        member = await db.find_club_member(club_id, user.id)        
        if not member or member.user_role != "OWNER":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        club_params = params.model_dump(exclude_unset=True)
        if club_params:
            #image = db.get_user_images(user.id, id=params.image_id) if params.image_id else None
            #if params.image_id is not None and not image:
            #    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Image not found")
            club = await db.update_club(club_id, **club_params)

    return ClubProfile(
        id=club.id, 
        name=club.name,
        description=club.description,
        image_id=club.image_id,
        user_role=member.user_role,
        user_approved=member.approved_ts is not None
    )


#@router.delete("/{club_id}", status_code=204, summary="Delete club")
#async def v1_delete_club(club_id: int, session_uuid: SessionUUID):
#    with DBI() as dbi:
#        _, user = get_session_and_user(dbi, session_uuid)
#        club = dbi.get_club(club_id)
#        if not club:
#            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
#        club_member = dbi.get_club_member(club_id, user.id)
#        if not club_member or club_member.user_role != "OWNER":
#            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
#        dbi.delete_club(club.id)
#
#    return {}


@router.get("/{club_id}/members", summary="Get club memebrs")
async def v1_get_club_members(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        members = await db.get_club_members(club_id=club.id)

    return list([
        ClubMemberProfile(
            id=member.id,
            #username=member.username,
            #image_id=member.image_id,
            user_role=member.user_role,
            user_approved=member.approved_ts is not None
        ) for member in members
    ])


@router.post("/{club_id}/members", summary="Submit join request")
async def v1_join_club(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        member = await db.find_club_member(club_id, user.id)
        if not member:
            member = await db.create_club_member(club.id, user.id, None)

    return ClubProfile(
        id=club.id, 
        name=club.name,
        description=club.description,
        user_role=member.user_role,
        user_approved=member.approved_ts is not None
    )


@router.put("/{club_id}/members/{member_id}", summary="Approve join request")
async def v1_approve_join_request(club_id: int, member_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        user_member = await db.find_club_member(club_id, user.id)
        if not user_member or user_member.user_role != "OWNER":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        member = await db.get_club_member(member_id)
        if not member or member.club_id!=club.id:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member not found")
        if member.approved_ts is None:
            member = await db.approve_club_member(member_id, user.id, None)
        new_member_profile = await db.get_user(member.user_id)

    return ClubMemberProfile(
        id=new_member_profile.id,
        username=new_member_profile.name,
        image_id=new_member_profile.image_id,
        user_role=member.user_role,
        user_approved=member.approved_ts is not None
    )


@router.post("/{club_id}/tables", status_code=201, summary="Create club table")
async def v1_create_club_table(club_id: int, params: TableParams, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        member = await db.find_club_member(club.id, user.id)
        if not member or member.user_role != 'OWNER':
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        kwargs = params.model_dump(exclude_unset=False)
        table = await db.create_table(club_id=club_id, **kwargs)
    
    return TableProfile(**table._asdict())

@router.get("/{club_id}/tables", status_code=200, summary="Get club tables")
async def v1_get_club_tables(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        member = await db.find_club_member(club.id, user.id)
        if not member:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        tables = await db.get_tables_for_club(club_id=club_id)

    return [TableProfile(**row._asdict()) for row in tables]

