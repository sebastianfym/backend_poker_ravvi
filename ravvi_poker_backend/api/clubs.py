from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
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
    founder_id: int
    name: str
    description: str|None = None
    user_role: str|None = None

@router.post("", response_model=ClubProfile, summary="Create new club")
async def v1_create_club(params: ClubProps, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.create_club(founder_id=user.id, name=params.name)

    return ClubProfile(
        id=club.id, 
        founder_id=club.founder_id, 
        name = club.name, description=club.description,
        user_role="OWNER"
        )

@router.get("", response_model=List[ClubProfile], summary="List clubs for current user")
async def v1_list_clubs(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        clubs = dbi.get_clubs_for_user(user_id=user.id)
    
    clubs = [
        ClubProfile(
            id=c.id, 
            founder_id=c.founder_id, 
            name = c.name, description=c.description,
            user_role="OWNER" if c.founder_id == user.id else None
        )        
        for c in clubs
    ]

    return clubs


@router.get("/{club_id}", response_model=ClubProfile, summary="Get club by id")
async def v1_get_club(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
    
    return ClubProfile(
        id=club.id, 
        founder_id=club.founder_id, 
        name = club.name, description=club.description,
        user_role="OWNER" if club.founder_id == user.id else None
        )
      
@router.put("/{club_id}", response_model=ClubProfile, summary="Update club profile")
async def v1_update_club(club_id: int, params: ClubProps, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if club.founder_id!=user.id:
            # TODO: proper error code
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid role")

        club = dbi.update_club(club_id, name=params.name, description=params.description)
    
    return ClubProfile(
        id=club.id, 
        founder_id=club.founder_id, 
        name = club.name, description=club.description,
        user_role="OWNER" if club.founder_id == user.id else None
        )


@router.post("/{club_id}/members", summary="Submit join request")
async def v1_club_join_request(club_id: int, session_uuid: RequireSessionUUID):
    
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        #TODO
    
    return {}

