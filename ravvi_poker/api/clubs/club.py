from logging import getLogger
from fastapi import Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from .utilities import check_rights_user_club_owner_or_manager
from ..users.types import black_list_symbols
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user, check_club_name
from .router import router
from .types import *

log = getLogger(__name__)


@router.post("", status_code=HTTP_201_CREATED, summary="Create new club")
async def v1_create_club(params: ClubProps, session_uuid: SessionUUID) -> ClubProfile:
    """
    Эндпоинт служит для создания клуба
    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        for symbol in black_list_symbols:
            try:
                if symbol in params.name:
                    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="You are using forbidden characters")
            except TypeError:
                break
        club = await db.create_club(user_id=user.id, name=params.name, description=params.description,
                                    image_id=params.image_id, timezone=params.timezone, )
    club_profile = ClubProfile(
        id=club.id,
        name=club.name,
        description=club.description,
        image_id=club.image_id,
        user_role="O",
        user_approved=True,
        timezone=club.timezone
    ).model_dump()
    for param in ["tables_count", "players_count", "user_balance", "agents_balance", "club_balance", "service_balance"]:
        club_profile.pop(param, None)
    return club_profile


@router.get("", summary="List clubs for current user")
async def v1_list_clubs(session_uuid: SessionUUID) -> List[ClubProfile]:
    """
    Служит для получения всех клубов доступных  пользователю
    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        clubs = await db.get_clubs_for_user(user_id=user.id)
        list_with_clubs = []
        for club in clubs:
            list_with_clubs.append(
                ClubProfile(
                    id=club.id,
                    name=club.name,
                    description=club.description,
                    image_id=club.image_id,
                    user_role=club.user_role,
                    user_approved=club.approved_ts is not None,
                    tables_count=club.tables_сount,
                    players_count=club.players_online,
                    user_balance=await db.get_user_balance_in_club(club_id=club.id, user_id=user.id),
                    agents_balance=await db.get_balance_shared_in_club(club_id=club.id, user_id=user.id),
                    club_balance=club.club_balance,
                    service_balance=await db.get_service_balance_in_club(club_id=club.id, user_id=user.id)
                )
            )

        return list_with_clubs
        # return list([
        #     ClubProfile(
        #         id=club.id,
        #         name=club.name,
        #         description=club.description,
        #         image_id=club.image_id,
        #         user_role=club.user_role,
        #         user_approved=club.approved_ts is not None,
        #         tables_count=club.tables_сount,
        #         players_count=club.players_online,
        #         user_balance=await db.get_user_balance_in_club(club_id=club.id, user_id=user.id),
        #         agents_balance=await db.get_balance_shared_in_club(club_id=club.id, user_id=user.id),
        #         club_balance=club.club_balance,
        #         service_balance=await db.get_service_balance_in_club(club_id=club.id, user_id=user.id)
        #     )
        # ])


@router.get("/{club_id}", summary="Get club by id",
            responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Club not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You are not a member in this club or account not been approved"}
            },
            )
async def v1_get_club(club_id: int, session_uuid: SessionUUID) -> ClubProfile:
    """
    Служит для получения детальной карточки клуба по id

    - **club_id**: number

    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_member(user_id=user.id, club_id=club_id)
#        if not account:
#            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You are not a member in this club")
#        if account.approved_ts is None:
#            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Your account not been approved")
        member_attributes = {}
        if account and account.approved_ts and not account.closed_ts:
            member_attributes = dict(
                club_balance=club.club_balance,
                user_balance=await db.get_user_balance_in_club(club_id=club.id, user_id=user.id),
                agents_balance=await db.get_balance_shared_in_club(club_id=club.id, user_id=user.id),
                service_balance=await db.get_service_balance_in_club(club_id=club.id, user_id=user.id),
            )
        return ClubProfile(
            id=club.id,
            name=club.name,
            description=club.description,
            image_id=club.image_id,
            user_role=account.user_role if account else None,
            user_approved=account.approved_ts is not None if account else None,
            tables_count=club.tables_сount,
            players_count=club.players_online,
            timezone=club.timezone,
            automatic_confirmation=club.automatic_confirmation,
            **member_attributes
        )


@router.patch("/{club_id}", summary="Обновление клуба", responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Club not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions for that action"}
            },
            )
async def v1_update_club(club_id: int, params: ClubProps, session_uuid: SessionUUID) -> ClubProfile:
    """
    Служит для обновления данных клуба

    - **club_id**: number

    """
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
            if 'name' in club_params.keys() and club_params['name'] is not None:
                club_name = club_params['name']
                for symbol in black_list_symbols:
                    if symbol in club_name:
                        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="You are using forbidden characters")
                if await db.check_uniq_club_name(club_name) is not None:
                    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This name is already taken")
                check_club_name(club_name, club_id)
            club = await db.update_club(club_id, **club_params)
    return ClubProfile(
        id=club.id,
        name=club.name,
        description=club.description,
        image_id=club.image_id,
        user_role=account.user_role,
        user_approved=account.approved_ts is not None,
        automatic_confirmation=club.automatic_confirmation
    )


@router.post("/{club_id}/leave_from_club", status_code=HTTP_200_OK, summary="Leave from club", responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Club or account not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "Owner can't leave your own club"}
            },
            )
async def v1_leave_from_club(club_id: int, session_uuid: SessionUUID):
    """
    Служит для выхода пользователя из клуба.
    Выйти из клуба может кто угодно, кроме владельца клуба.

    - **club_id**: number

    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")

        account = await db.find_account(user_id=user.id, club_id=club_id)
        if not account or account.closed_ts is not None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Account not found")
        if account.user_role == "O":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You can't leave your own club")
        await db.close_club_member(account.id, user.id, None)
        return HTTP_200_OK


@router.get("/{club_id}/club_balance", status_code=HTTP_200_OK,
            summary="Получить все допустимые типы балансов (суммарные) для клуба: агентский баланс, баланс пользователей, баланс клуба",
            responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Club not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions"}
            },
            )
async def v1_get_all_club_balance(club_id: int, users=Depends(check_rights_user_club_owner_or_manager)) -> ClubBalance:
    """
    Служит для получения всех типов баланса для клуба.

    - **club_id**: number

    """
    async with DBI() as db:
        _, _, club = users
        club_balance = club.club_balance
        club_members = []

        for member in await db.get_club_members(club_id):
            if member.user_role == 'A' or member.user_role == "S":
                balance_shared = member.balance_shared
            else:
                balance_shared = None
            club_members.append(ClubMemberProfile(
                balance=member.balance,
                balance_shared=balance_shared
            ))

        members_balance = sum(user.balance for user in club_members)
        shared_balance = sum(user.balance_shared for user in club_members if user.balance_shared is not None)
        total_balance = members_balance + shared_balance

    return ClubBalance(
        club_balance=club_balance,
        members_balance=members_balance,
        agents_balance=shared_balance,
        total_balance=total_balance,
    )






