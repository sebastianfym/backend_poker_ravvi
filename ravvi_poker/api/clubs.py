from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
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
    user_role: str|None
    user_approved: bool


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
        club_user = dbi.get_club_user(club_id, user.id)
    
    return ClubProfile(
        id=club.id, 
        name = club.name, 
        description=club.description,
        user_role = club_user.user_role if club_user else None,
        user_approved = club_user.approved_ts is not None if club_user else None
        )
      
@router.put("/{club_id}", response_model=ClubProfile, summary="Update club profile")
async def v1_update_club(club_id: int, params: ClubProps, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_user = dbi.get_club_user(club_id, user.id)        
        if not club_user or club_user.user_role!="OWNER":
            # TODO: proper error code
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid role")
        club = dbi.update_club(club_id, name=params.name, description=params.description)
    
    return ClubProfile(
        id=club.id, 
        name = club.name, 
        description=club.description,
        user_role = club_user.user_role if club_user else None,
        user_approved = club_user.approved_ts is not None if club_user else None
        )


@router.post("/{club_id}/members", summary="Submit join request")
async def v1_club_join_request(club_id: int, session_uuid: RequireSessionUUID):
    
    user_role='PLAYER'
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_user = dbi.create_join_club_request(club_id=club.id, user_id=user.id, user_role=user_role)
    
    return ClubProfile(
        id=club.id, 
        name = club.name, description=club.description,
        user_role = club_user.user_role if club_user else None,
        user_approved = club_user.approved_ts is not None if club_user else None
        )

