from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_200_OK, HTTP_201_CREATED
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
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


@router.post("", status_code=HTTP_201_CREATED, summary="Create new club")
async def v1_create_club(params: ClubProps, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.create_club(user_id=user.id, name=params.name, description=params.description, image_id=params.image_id)

    return ClubProfile(
        id=club.id, 
        name=club.name, 
        description=club.description,
        image_id=club.image_id,
        user_role="O",
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
        account = await db.find_account(user_id=user.id, club_id=club_id)

    return ClubProfile(
        id=club.id,
        name=club.name,
        description=club.description,
        image_id=club.image_id,
        user_role=account.user_role if account else None,
        user_approved=account.approved_ts is not None if account else None
    )


@router.patch("/{club_id}", summary="Update club")
async def v1_update_club(club_id: int, params: ClubProps, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)        
        if not account or account.user_role != "O":
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
        user_role=account.user_role,
        user_approved=account.approved_ts is not None
    )


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
        account = await db.find_account(user_id=user.id, club_id=club_id)
        if not account:
            account = await db.create_club_member(club.id, user.id, None)

    return ClubProfile(
        id=club.id, 
        name=club.name,
        description=club.description,
        user_role=account.user_role,
        user_approved=account.approved_ts is not None
    )


@router.put("/{club_id}/members/{member_id}", summary="Approve join request")
async def v1_approve_join_request(club_id: int, member_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        if not account or account.user_role != "O":
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


@router.post("/{club_id}/tables", status_code=HTTP_201_CREATED, summary="Create club table")
async def v1_create_club_table(club_id: int, params: TableParams, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        if not account or account.user_role != 'O':
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        if params.table_type not in ('RG', 'SNG', 'MTT'):
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid table type")
        kwargs = params.model_dump(exclude_unset=False)
        main_parameters = ["club_id", "table_type", "table_name", "table_seats", "game_type", "game_subtype"]

        table_type = kwargs.get('table_type')#.value
        table_name = kwargs.get('table_name')
        table_seats = kwargs.get('table_seats')
        game_type = kwargs.get('game_type')#.value
        game_subtype = kwargs.get('game_subtype')

        for param in ["players_count", "viewers_count", "created", "opened", "closed"]:
            try:
                del kwargs[param]
            except KeyError:
                continue
        kwargs = {key: value for key, value in kwargs.items() if key not in main_parameters}

        table = await db.create_table(club_id=club_id, table_type=table_type, table_name=table_name,
                                      table_seats=table_seats, game_type=game_type, game_subtype=game_subtype,
                                      props=kwargs)
    row_dict = dict(table._asdict())
    props_dict = row_dict.pop('props', {})

    row_dict.update(props_dict)

    return TableProfile(**row_dict)


@router.get("/{club_id}/tables", status_code=HTTP_200_OK, summary="Get club tables")
async def v1_get_club_tables(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        if not account:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        tables = await db.get_club_tables(club_id=club_id)
    result = []
    for row in tables:
        row_dict = dict(row._asdict())
        props_dict = row_dict.pop('props', {})

        row_dict.update(props_dict)
        try:
            entry = TableProfile(**row_dict)
            result.append(entry)
        except Exception as ex:
            pass
    return result

