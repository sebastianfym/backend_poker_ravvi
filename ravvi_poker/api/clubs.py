from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel
from . import utils

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

router = APIRouter(prefix="/clubs", tags=["clubs"])


class ClubProps(BaseModel):
    name: str
    description: str|None = None


class ClubProfile(BaseModel):
    id: int
    name: str
    description: str|None = None
    user_role: str|None = None
    user_approved: bool


class ClubMemberProfile(BaseModel):
    id: int | None = None
    username: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool | None = None


@router.post("", response_model=ClubProfile, summary="Create new club")
async def v1_create_club(params: ClubProps, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.create_club(founder_id=user.id, name=params.name)

    return ClubProfile(
        id=club.id, 
        name = club.name, 
        description=club.description,
        user_role="OWNER",
        user_approved=True
        )

@router.get("", response_model=List[ClubProfile], summary="List clubs for current user")
async def v1_list_clubs(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        clubs = dbi.get_clubs_for_user(user_id=user.id)
    
    clubs = [
        ClubProfile(
            id=c.id, 
            name = c.name, 
            description=c.description,
            user_role=c.user_role,
            user_approved = c.approved_ts is not None
        )        
        for c in clubs
    ]

    return clubs


@router.get("/{club_id}", response_model=ClubProfile, summary="Get club by id")
async def v1_get_club(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_member = dbi.get_club_member(club_id, user.id)
    
    return ClubProfile(
        id=club.id, 
        name = club.name, 
        description=club.description,
        user_role = club_member.user_role if club_member else None,
        user_approved = club_member.approved_ts is not None if club_member else None
        )
      
@router.put("/{club_id}", response_model=ClubProfile, summary="Update club profile")
async def v1_update_club(club_id: int, params: ClubProps, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_member = dbi.get_club_member(club_id, user.id)        
        if not club_member or club_member.user_role!="OWNER":
            # TODO: proper error code
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid role")
        club = dbi.update_club(club_id, name=params.name, description=params.description)
    
    return ClubProfile(
        id=club.id, 
        name = club.name, 
        description=club.description,
        user_role = club_member.user_role if club_member else None,
        user_approved = club_member.approved_ts is not None if club_member else None
        )


@router.get("/{club_id}/members", summary="Get club memebrs")
async def v1_get_club_members(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_members = dbi.get_club_members(club_id=club.id)

    return list([
        ClubMemberProfile(
            id=member.id,
            username=member.username,
            image_id=member.image_id,
            user_role=member.user_role,
            user_approved=member.approved_ts is not None
        ) for member in club_members
    ])


@router.post("/{club_id}/members", summary="Submit join request")
async def v1_join_club(club_id: int, session_uuid: RequireSessionUUID):
    DEFAULT_USER_ROLE = "PLAYER"
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        new_member = dbi.get_club_member(club_id, user.id)
        if not new_member:
            new_member = dbi.create_join_club_request(
                club_id=club.id, user_id=user.id, user_role=DEFAULT_USER_ROLE
            )

    return ClubProfile(
        id=club.id, 
        name=club.name,
        description=club.description,
        user_role=new_member.user_role,
        user_approved=new_member.approved_ts is not None
    )


@router.post("/{club_id}/members/{member_id}", summary="Approve join request")
async def v1_approve_join_request(club_id: int, member_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        new_member = dbi.get_club_member(club_id, member_id)
        if not new_member:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member not found")
        user_member = dbi.get_club_member(club_id, user.id)        
        if not user_member or user_member.user_role != "OWNER":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        new_member = dbi.approve_club_member(club.id, user.id, member_id)
        new_member_profile = dbi.get_user(id=new_member.user_id)

    return ClubMemberProfile(
        id=new_member_profile.id,
        username=new_member_profile.username,
        image_id=new_member_profile.image_id,
        user_role=new_member.user_role,
        user_approved=new_member.approved_ts is not None
    )


@router.delete("/{club_id}/members/{member_id}", status_code=204, summary="Delete club member")
async def v1_delete_club_member(club_id: int, member_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        member = dbi.get_club_member(club_id, member_id)
        if not member:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member not found")
        user_member = dbi.get_club_member(club_id, user.id) 
        if not user_member or user_member.user_role != "OWNER":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        # TODO realize method
        dbi.delete_club_member(club.id, member_id)

    return {}
