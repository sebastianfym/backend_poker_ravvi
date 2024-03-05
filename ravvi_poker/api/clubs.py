import datetime
import decimal
import json
import time
from decimal import Decimal
from typing import Annotated, Any, List
from logging import getLogger
from fastapi import APIRouter, Request, Depends
from fastapi.exceptions import HTTPException
from psycopg.rows import Row
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_418_IM_A_TEAPOT
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from pydantic import BaseModel, Field, field_validator, validator

from ..db import DBI
from .utils import SessionUUID, get_session_and_user
from .tables import TableParams, TableProfile

log = getLogger(__name__)

router = APIRouter(prefix="/clubs", tags=["clubs"])


class ClubProps(BaseModel):
    name: str | None = None
    description: str | None = None
    image_id: int | None = None
    timezone: str | None = None


class ClubProfile(BaseModel):
    id: int
    name: str
    description: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool | None = None

    tables_count: int | None = 0
    players_count: int | None = 0
    user_balance: float | None = 0.00
    agents_balance: float | None = 0.00
    club_balance: float | None = 0.00
    service_balance: float | None = 0.00

    timezone: str | None = None


class ClubMemberProfile(BaseModel):
    id: int | None = None
    username: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool | None = None
    country: str | None = None

    nickname: str | None = None
    balance: float | None = 00.00
    balance_shared: float | None = 00.00

    join_in_club: float | None = None
    leave_from_club: float | None = None

    last_session: float | None = None
    last_game: float | None = None

    winning: float | None = 00.00
    hands: float | None = 00.00
    user_comment: str | None = None


class UserRequest(BaseModel):
    id: int | None
    txn_id: int | None

    username: str | None
    image_id: int | None
    user_role: str | None
    nickname: str | None
    txn_value: float | None
    txn_type: str | None
    balance_type: str | None

    join_in_club: float | None
    leave_from_club: float | None

    country: str | None


class UnionProfile(BaseModel):
    name: str | None = None
    """По мере прогресса раширить модель"""


class AccountDetailInfo(BaseModel):
    join_datestamp: float | None
    timezone: str | None
    table_types: set | None
    game_types: set | None
    game_subtypes: set | None
    opportunity_leave: bool | None = True
    hands: float | None
    winning: float | None
    bb_100_winning: float | None
    now_datestamp: float | None


class MemberAccountDetailInfo(BaseModel):
    join_datestamp: float | None
    las_entrance_in_club: float | None
    last_game: float | None
    timezone: str | None
    opportunity_leave: bool | None = True
    nickname: str | None
    country: str | None
    user_role: str | None
    club_comment: str | None
    balance: float | None
    balance_shared: float | None
    hands: float | None
    winning: float | None
    bb_100_winning: float | None
    now_datestamp: float | None


class ChangeMembersData(BaseModel):
    user_id: int
    nickname: str | None = None
    club_comment: str | None = None
    user_role: str | None = None

    @validator("user_role")
    def user_role_validate(cls, value):
        if value not in ['O', 'M', 'A', 'P', 'S']:
            raise ValueError('Operation must be either "approve" or "reject"')
        return value


class ClubChipsValue(BaseModel):
    amount: Decimal = Field(
        gt=0,
        lt=10 ** 10,
        decimal_places=2
    )

    @field_validator("amount", mode="before")
    @classmethod
    def ensure_not_str(cls, v: Any):
        if isinstance(v, str):
            raise ValueError
        return v


class UserChipsValue(ClubChipsValue):
    balance: str
    # ID аккаунта внутри клуба
    account_id: int
    user_account: Row | None = Field(default=None)

    @field_validator("balance", mode="before")
    @classmethod
    def ensure_correct_type(cls, v: Any):
        if v not in ["balance", "balance_shared"]:
            raise ValueError
        return v


class ChipRequestForm(BaseModel):
    id: int
    operation: str

    @validator('operation')
    def operation_validate(cls, value):
        if value not in ["approve", "reject"]:
            raise ValueError('Operation must be either "approve" or "reject"')
        return value


class ClubHistoryTransaction(BaseModel):
    txn_type: str | None
    txn_value: float | None
    txn_time: float | None
    recipient_id: int | None
    recipient_name: str | None
    recipient_nickname: str | None
    recipient_country: str | None
    recipient_role: str | None

    sender_id: int | None
    sender_name: str | None
    sender_nickname: str | None
    sender_country: str | None
    sender_role: str | None
    balance_type: str | None


class UserRequestsToJoin(BaseModel):
    rakeback: int | None = None
    agent_id: int | None = None
    nickname: str | None = None
    comment: str | None = None
    user_role: str | None = "P"

    @validator("user_role")
    def user_role_validate(cls, value):
        if value not in ['O', 'M', 'A', 'P', 'S']:
            raise ValueError('Operation must be either "approve" or "reject"')
        return value


async def check_rights_user_club_owner(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif club.closed_ts:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        club_owner_account = await db.find_account(user_id=user.id, club_id=club_id)
        if club_owner_account is None or club_owner_account.user_role != "O":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")

    return club_owner_account, user, club


async def check_rights_user_club_owner_or_manager(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif club.closed_ts:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        club_owner_account = await db.find_account(user_id=user.id, club_id=club_id)
        if club_owner_account is None or club_owner_account.user_role.lower() not in ['o', 'm']:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action.")
        return club_owner_account, user, club


@router.post("", status_code=HTTP_201_CREATED, summary="Create new club")
async def v1_create_club(params: ClubProps, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.create_club(user_id=user.id, name=params.name, description=params.description,
                                    image_id=params.image_id, timezone=params.timezone)
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
async def v1_list_clubs(session_uuid: SessionUUID):
    # TODO только список клубов в которых он активен
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
                user_approved=club.approved_ts is not None,
                tables_count=club.tables_сount,
                players_count=club.players_online,
                user_balance=await db.get_user_balance_in_club(club_id=club.id, user_id=user.id),
                agents_balance=await db.get_balance_shared_in_club(club_id=club.id, user_id=user.id),
                # TODO почему пользователь видит баланс клуба в независимости от роли?!?!?
                club_balance=club.club_balance,
                service_balance=await db.get_service_balance_in_club(club_id=club.id, user_id=user.id)
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
        if account.approved_ts is None:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Your account not been approved")
        return ClubProfile(
            id=club.id,
            name=club.name,
            description=club.description,
            image_id=club.image_id,
            user_role=account.user_role if account else None,
            user_approved=account.approved_ts is not None if account else None,
            club_balance=club.club_balance,
            tables_count=club.tables_сount,
            players_count=club.players_online,
            user_balance=await db.get_user_balance_in_club(club_id=club.id, user_id=user.id),
            agents_balance=await db.get_balance_shared_in_club(club_id=club.id, user_id=user.id),
            service_balance=await db.get_service_balance_in_club(club_id=club.id, user_id=user.id),
            timezone=club.timezone
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
            # image = db.get_user_images(user.id, id=params.image_id) if params.image_id else None
            # if params.image_id is not None and not image:
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
        result_list = []
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        members = await db.get_club_members(club_id=club.id)
        for member in members:
            if member.closed_ts is not None or member.approved_ts is None:
                continue
            user = await db.get_user(id=member.user_id)
            if member.user_role not in ["A", "S"]:
                balance_shared = None
            else:
                balance_shared = member.balance_shared

            last_login_id = (await db.get_last_user_login(member.user_id)).id
            last_session = await db.get_last_user_session(last_login_id)

            table_id_list = [table.id for table in await db.get_club_tables(club_id)]

            all_user_games_id = [game.game_id for game in (await db.get_games_player_through_user_id(user.id))]

            if len(all_user_games_id) != 0:
                hands = len(await db.statistics_all_games_users_in_club(all_user_games_id, table_id_list))
                last_game = max(await db.statistics_all_games_users_in_club(all_user_games_id, table_id_list), key=lambda x: x.id)
                last_game_time=last_game.begin_ts.timestamp()
            else:
                hands = 0
                last_game_time = 0

            winning_row = await db.get_all_account_txns(member.id)

            sum_all_buyin = sum(
                [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'BUYIN']])
            sum_all_cashout = sum(
                [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'CASHOUT']])
            winning = sum_all_cashout - abs(sum_all_buyin)

            member = ClubMemberProfile(
                id=user.id, # member.id --- если нужно использовать старый функционал кассы
                username=user.name,
                image_id=user.image_id,
                user_role=member.user_role,
                user_approved=member.approved_ts is not None,
                country=user.country,
                balance=member.balance,
                balance_shared=balance_shared,
                join_in_club=member.created_ts.timestamp(),
                last_session=last_session.created_ts.timestamp(),
                last_game=last_game_time,
                winning=winning,
                hands=hands
            )
            result_list.append(member)
        return result_list


@router.post("/{club_id}/members", summary="Submit join request")
async def v1_join_club(club_id: int, session_uuid: SessionUUID, request: Request):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        try:
            user_comment = (await request.json())['user_comment']
        except json.decoder.JSONDecodeError:
            user_comment = None
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        if not account:
            account = await db.create_club_member(club.id, user.id, user_comment)
        elif account.closed_ts is not None and account.club_id == club_id:
            await db.refresh_member_in_club(account.id, user_comment)

    return ClubProfile(
        id=club.id,
        name=club.name,
        description=club.description,
        user_role=account.user_role,
        # TODO а зачем? тут всегда True
        user_approved=account.approved_ts is not None
    )


@router.put("/{club_id}/members/{user_id}", summary="Принимает заявку на вступление в клуб")
async def v1_approve_join_request(club_id: int, user_id: int, params: UserRequestsToJoin, users=Depends(check_rights_user_club_owner)):
    agent_id = params.agent_id
    rakeback = params.rakeback
    nickname = params.nickname
    comment = params.comment
    user_role = params.user_role

    _, owner, club = users
    async with DBI() as db:
        member = await db.find_account(user_id=user_id, club_id=club_id)
        if not member:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member not found")

        if not member or member.club_id != club.id:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member not found")
        if member.approved_ts is None:
            member = await db.approve_club_member(member.id, owner.id, comment, nickname, user_role)
            new_member_profile = await db.get_user(member.user_id)
            return ClubMemberProfile(
                id=new_member_profile.id,
                username=new_member_profile.name,
                image_id=new_member_profile.image_id,
                user_role=member.user_role,
                user_approved=member.approved_ts is not None
            )
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="An unexpected error has occurred")


@router.delete("/{club_id}/members/{user_id}", status_code=HTTP_200_OK, summary="Отклоняет заявку на вступление в клуб")
async def v1_reject_join_request(club_id: int, user_id: int, users=Depends(check_rights_user_club_owner_or_manager)):
    _, owner, club = users
    async with DBI() as db:
        member = await db.find_account(user_id=user_id, club_id=club_id)
        if not member:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member not found")

        if not member or member.club_id != club.id:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member not found")
        await db.close_club_member(member.id, owner.id, None)
        return HTTP_200_OK


@router.get("/{club_id}/members/requests", status_code=HTTP_200_OK,
            summary="Отображение всех заявок на вступление в клуб")
async def v1_requests_to_join_in_club(club_id: int, users=Depends(check_rights_user_club_owner)):
    result_list = []

    async with DBI() as db:
        not_approved_members = await db.requests_to_join_in_club(users[2].id)
        for member in not_approved_members:
            user = await db.get_user(id=member.user_id)
            potential_member = ClubMemberProfile(
                id=user.id,
                username=user.name,
                image_id=user.image_id,
                country=user.country,
                user_comment=member.user_comment
            )
            result_list.append(potential_member)
        return result_list


@router.post("/{club_id}/tables", status_code=HTTP_201_CREATED, summary="Create club table")
async def v1_create_club_table(club_id: int, params: TableParams, session_uuid: SessionUUID, request: Request):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")

        json_data = await request.json()

        invalid_params = set(json_data.keys()) - set(params.__annotations__.keys())
        if invalid_params:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                detail=f"Invalid parameters: {', '.join(invalid_params)}")

        account = await db.find_account(user_id=user.id, club_id=club_id)
        if not account or account.user_role != 'O':
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        if params.table_type not in ('RG', 'SNG', 'MTT'):
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid table type")
        kwargs = params.model_dump(exclude_unset=False)
        main_parameters = ["club_id", "table_type", "table_name", "table_seats", "game_type", "game_subtype"]

        table_type = kwargs.get('table_type')
        table_name = kwargs.get('table_name')
        table_seats = kwargs.get('table_seats')
        game_type = kwargs.get('game_type')
        game_subtype = kwargs.get('game_subtype')

        for param in ["players_count", "viewers_count", "created", "opened", "closed"]:
            try:
                del kwargs[param]
            except KeyError:
                continue
        kwargs = {key: value for key, value in kwargs.items() if key not in main_parameters}

        # TODO а нельзя params.get_main_params() и params_get_pops()
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
        # TODO исключенному игроку показываем столы?
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


@router.post("/{club_id}/add_chip_on_club_balance", status_code=HTTP_200_OK,
             summary="Adds a certain number of chips to the club's balance")
async def v1_add_chip_on_club_balance(club_id: int, chips_value: ClubChipsValue,
                                      users=Depends(check_rights_user_club_owner)):
    club_owner_account, user, _ = users
    async with DBI() as db:
        await db.txn_with_chip_on_club_balance(club_id, chips_value.amount, "CASHIN", club_owner_account.id, user.id)


@router.post("/{club_id}/delete_chip_from_club_balance", status_code=HTTP_200_OK,
             summary="Take away a certain number of chips from the club's balance")
async def v1_delete_chip_from_club_balance(club_id: int, chips_value: ClubChipsValue,
                                           users=Depends(check_rights_user_club_owner)):
    club_owner_account, user = users[0], users[1]
    async with DBI() as db:
        await db.txn_with_chip_on_club_balance(club_id, chips_value.amount, "REMOVE", club_owner_account.id, user.id)


async def check_compatibility_recipient_and_balance_type(club_id: int, request: UserChipsValue):
    async with DBI() as db:
        user_account = await db.find_account(user_id=request.account_id, club_id=club_id)
    try:
        if user_account.user_role not in ["A", "S"] and request.balance == "balance_shared":
            raise ValueError
        request.user_account = user_account
        return request
    except AttributeError:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='User account not found in club')


@router.post("/{club_id}/giving_chips_to_the_user", status_code=HTTP_200_OK,
             summary="Owner giv chips to the club's user")
async def v1_club_giving_chips_to_the_user(club_id: int, request: Annotated[
    UserChipsValue, Depends(check_compatibility_recipient_and_balance_type)],
                                           users=Depends(check_rights_user_club_owner)):
    async with DBI() as db:
        await db.giving_chips_to_the_user(request.amount, request.account_id, request.balance, users[0].id)


@router.post("/{club_id}/delete_chips_from_the_user", status_code=HTTP_200_OK,
             summary="Owner take away chips from the club's user")
async def v1_club_delete_chips_from_the_user(club_id: int, request: Annotated[
    UserChipsValue, Depends(check_compatibility_recipient_and_balance_type)],
                                             users=Depends(check_rights_user_club_owner)):
    async with DBI() as db:
        if request.balance == "balance":
            await db.delete_chips_from_the_account_balance(request.amount, request.account_id, users[0].id)
        else:
            await db.delete_chips_from_the_agent_balance(request.amount, request.account_id, users[0].id)


@router.post("/{club_id}/request_chips", status_code=HTTP_200_OK, summary="The user requests chips from the club")
async def v1_requesting_chips_from_the_club(club_id: int, session_uuid: SessionUUID, request: Request):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        try:
            if account.approved_ts is None or account.approved_ts is False:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Your account has not been verified")
        except AttributeError:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")

        check_last_request = await db.check_request_to_replenishment(account.id)

        try:
            if check_last_request.props['status'] == 'consider':
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                    detail="Your request is still under consideration")
        except AttributeError:
            pass

        json_data = await request.json()

        try:
            amount = json_data["amount"]
            balance = json_data["balance"]
        except KeyError as e:
            return HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"You forgot to add a value: {e}")
        if account.user_role not in ["A", "S"] and balance == "balance_shared":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You don't have enough permissions to work "
                                                                       "with agent balance")

        await db.send_request_for_replenishment_of_chips(account_id=account.id, amount=amount, balance=balance)
        return HTTP_200_OK


@router.post("/{club_id}/leave_from_club", status_code=HTTP_200_OK, summary="Leave from club")
async def v1_leave_from_club(club_id: int, session_uuid: SessionUUID):
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


@router.post("/{club_id}/profile/{user_id}", status_code=HTTP_200_OK,
             summary="Страница с информацией о конкретном участнике клуба для админа")
async def v1_user_account(club_id: int, user_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        owner = await db.find_account(user_id=user.id, club_id=club_id)
        account = await db.find_account(user_id=user_id, club_id=club_id)
        if not account:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Such a user is not a member of the club")
        if user.id != user_id and owner is None:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You dont have permission")
        if user.id != user_id and owner.user_role not in ["O", "M"]:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You dont have permission")

        opportunity_leave = True
        if account.user_role == "O":
            opportunity_leave = False
        if not account or account.closed_ts is not None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Account not found")

        table_id_list = [table.id for table in await db.get_club_tables(club_id)]

        time_obj = datetime.datetime.fromisoformat(str(account.created_ts))
        unix_time = int(time.mktime(time_obj.timetuple()))
        now_datestamp = int(time.mktime(datetime.datetime.fromisoformat(str(datetime.datetime.utcnow())).timetuple()))

        date_now = str(datetime.datetime.now()).split(" ")[0]
        table_types = []
        game_types = []
        game_subtype = []
        count_of_games_played = 0

        for table_id in table_id_list:
            for game in await db.statistics_of_games_played(table_id, date_now):
                count_of_games_played += 1
                table_types.append((await db.get_table(game.table_id)).table_type)
                game_types.append(game.game_type)
                game_subtype.append(game.game_subtype)

        winning_row = await db.get_statistics_about_winning(account.id, date_now)
        sum_all_buyin = sum(
            [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'BUYIN']])
        sum_all_cashout = sum(
            [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'CASHOUT']])
        winning = sum_all_cashout - abs(sum_all_buyin)

        bb_100_winning = 0

        all_games_id = [id.game_id for id in await db.all_players_games(user.id)]  # user.id
        access_games = []
        access_game_id = []

        for game_id in all_games_id:
            game = await db.check_game_by_date(game_id, date_now)
            if game is not None:
                access_games.append(game)
                access_game_id.append(game.id)

        game_props_list = []
        for game_id in access_game_id:
            balance_data = await db.get_balance_begin_and_end_from_game(game_id, user.id)  #
            game_data = await db.get_game_and_players(game_id)
            if balance_data.balance_end:
                balance_end = balance_data.balance_end
            game_props_list.append({'game_id': game_id, 'balance_begin': balance_data.balance_begin,
                                    'balance_end': balance_end,
                                    'big_blind': game_data[0].props['blind_big']})
        blind_big_dict = {}
        for item in game_props_list:
            big_blind = item['big_blind']
            balance_difference = item['balance_end'] - item['balance_begin']
            if big_blind in blind_big_dict:
                blind_big_dict[big_blind]['sum_winning'] += balance_difference
                blind_big_dict[big_blind]['count'] += 1
            else:
                blind_big_dict[big_blind] = {'big_blind': big_blind, 'sum_winning': balance_difference,
                                             'count': 1}
        result_list = list(blind_big_dict.values())

        quantity_games = 0
        for winning_100 in result_list:
            bb_100_winning += winning_100['sum_winning'] / decimal.Decimal(winning_100['big_blind'])
            quantity_games += winning_100['count']

        try:
            bb_100_winning /= quantity_games
            bb_100_winning *= 100
            bb_100 = round(bb_100_winning, 2)
        except ZeroDivisionError:
            bb_100 = 0

        last_login_id = (await db.get_last_user_login(user_id)).id
        last_session = await db.get_last_user_session(last_login_id)
        #Todo изменить значение у поля las_entrance_in_club на актуальную последнюю дату входа в клуб

        user_profile = await db.get_user(id=user_id)
        all_user_games_id = [game.game_id for game in (await db.get_games_player_through_user_id(user.id))]

        if len(all_user_games_id) != 0:
            last_game = max(await db.statistics_all_games_users_in_club(all_user_games_id, table_id_list),
                            key=lambda x: x.id)
            last_game_time = last_game.begin_ts.timestamp()
        else:
            last_game_time = None

        return MemberAccountDetailInfo(
            join_datestamp=unix_time,
            now_datestamp=now_datestamp,
            timezone=club.timezone,
            last_game=last_game_time,
            las_entrance_in_club=last_session.created_ts.timestamp(),
            nickname=account.nickname,
            country=user_profile.country,
            club_comment=account.club_comment,
            user_role=account.user_role,
            balance=account.balance,
            balance_shared=account.balance_shared,
            opportunity_leave=opportunity_leave,
            hands=count_of_games_played,  # todo потом добавить триггеры
            winning=winning,
            bb_100_winning=bb_100
        )


@router.post("/{club_id}/user_account", status_code=HTTP_200_OK,
             summary="Страница с информацией о конкретном участнике клуба")
async def v1_detail_account(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        opportunity_leave = True
        if account.user_role == "O":
            opportunity_leave = False
        if not account or account.closed_ts is not None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Account not found")

        table_id_list = [table.id for table in await db.get_club_tables(club_id)]

        time_obj = datetime.datetime.fromisoformat(str(account.created_ts))
        unix_time = int(time.mktime(time_obj.timetuple()))
        now_datestamp = int(time.mktime(datetime.datetime.fromisoformat(str(datetime.datetime.utcnow())).timetuple()))

        date_now = str(datetime.datetime.now()).split(" ")[0]
        table_types = []
        game_types = []
        game_subtype = []
        count_of_games_played = 0

        for table_id in table_id_list:
            for game in await db.statistics_of_games_played(table_id, date_now):
                count_of_games_played += 1
                table_types.append((await db.get_table(game.table_id)).table_type)
                game_types.append(game.game_type)
                game_subtype.append(game.game_subtype)

        winning_row = await db.get_statistics_about_winning(account.id, date_now)
        sum_all_buyin = sum(
            [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'BUYIN']])
        sum_all_cashout = sum(
            [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'CASHOUT']])
        winning = sum_all_cashout - abs(sum_all_buyin)

        bb_100_winning = 0

        all_games_id = [id.game_id for id in await db.all_players_games(user.id)]  # user.id
        access_games = []
        access_game_id = []

        for game_id in all_games_id:
            game = await db.check_game_by_date(game_id, date_now)
            if game is not None:
                access_games.append(game)
                access_game_id.append(game.id)

        game_props_list = []
        for game_id in access_game_id:
            balance_data = await db.get_balance_begin_and_end_from_game(game_id, user.id)  #
            game_data = await db.get_game_and_players(game_id)
            if balance_data.balance_end:
                balance_end = balance_data.balance_end
            game_props_list.append({'game_id': game_id, 'balance_begin': balance_data.balance_begin,
                                    'balance_end': balance_end,
                                    'big_blind': game_data[0].props['blind_big']})
        blind_big_dict = {}
        for item in game_props_list:
            big_blind = item['big_blind']
            balance_difference = item['balance_end'] - item['balance_begin']
            if big_blind in blind_big_dict:
                blind_big_dict[big_blind]['sum_winning'] += balance_difference
                blind_big_dict[big_blind]['count'] += 1
            else:
                blind_big_dict[big_blind] = {'big_blind': big_blind, 'sum_winning': balance_difference,
                                             'count': 1}
        result_list = list(blind_big_dict.values())

        quantity_games = 0
        for winning_100 in result_list:
            bb_100_winning += winning_100['sum_winning'] / decimal.Decimal(winning_100['big_blind'])
            quantity_games += winning_100['count']

        try:
            bb_100_winning /= quantity_games
            bb_100_winning *= 100
            bb_100 = round(bb_100_winning, 2)
        except ZeroDivisionError:
            bb_100 = 0
        return AccountDetailInfo(
            join_datestamp=unix_time,
            now_datestamp=now_datestamp,
            timezone=club.timezone,
            table_types=set(table_types),
            game_types=set(game_types),
            game_subtypes=set(game_subtype),
            opportunity_leave=opportunity_leave,
            hands=count_of_games_played,  # todo потом добавить триггеры
            winning=winning,
            bb_100_winning=bb_100
        )

@router.get("/{club_id}/club_balance", status_code=HTTP_200_OK,
            summary="Получить все допустимые типы балансов (суммарные) для клуба: агентский баланс, баланс пользователей, баланс клуба")
async def v1_get_all_club_balance(club_id: int, users=Depends(check_rights_user_club_owner_or_manager)):
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

    return {
        "club_balance": club_balance,
        "members_balance": members_balance,
        "agents_balance": shared_balance,
        "total_balance": total_balance,
    }


@router.get("/{club_id}/requests_chip_replenishment", status_code=HTTP_200_OK,
            summary="Получение списка с запросами на пополнение баланса")
async def v1_get_requests_for_chips(club_id: int, users=Depends(check_rights_user_club_owner)):
    sum_txn_value = 0
    all_users_requests = []
    result_dict = {"sum_txn_value": sum_txn_value, "users_requests": all_users_requests}
    async with DBI() as db:
        for member in await db.get_club_members(club_id):
            try:
                leave_from_club = datetime.datetime.timestamp(member.closed_ts)
            except TypeError:
                leave_from_club = None
            try:
                txn = await db.get_user_requests_to_replenishment(member.id)
                user = await db.get_user(id=member.user_id)
                result_dict['users_requests'].append(
                    UserRequest(
                        id=member.id,
                        txn_id=txn.id,
                        username=user.name,
                        nickname=member.nickname,
                        user_role=member.user_role,
                        image_id=(await db.get_user_image(member.user_id)).image_id,
                        txn_value=txn.txn_value,
                        txn_type=txn.txn_type,
                        balance_type=txn.props.get("balance"),
                        join_in_club=datetime.datetime.timestamp(member.created_ts),
                        leave_from_club=leave_from_club,
                        country=user.country
                    )
                )
                result_dict['sum_txn_value'] += txn.txn_value

            except AttributeError:
                continue
        return result_dict


@router.post("/{club_id}/action_with_user_request", status_code=HTTP_200_OK,
             summary='Подтвердить или отклонить пользовательские запросы на пополнение баланса')
async def v1_action_with_user_request(club_id: int, request_for_chips: ChipRequestForm,
                                      users=Depends(check_rights_user_club_owner)):
    club_owner_account = users[0]
    club = users[2]
    club_balance = club.club_balance
    request_for_chips = request_for_chips.model_dump()
    async with DBI() as db:
        if request_for_chips["operation"] == "approve":
            txn = await db.get_specific_txn(request_for_chips['id'])
            if club_balance - txn.txn_value < 0:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Club balance cannot be less than 0')

            await db.giving_chips_to_the_user(txn.txn_value, txn.account_id, txn.props["balance"],
                                              club_owner_account.id)
            await db.update_status_txn(txn.id, "approve")
            await db.refresh_club_balance(club_id, txn.txn_value, "give_out")
        elif request_for_chips["operation"] == "reject":
            txn = await db.get_specific_txn(request_for_chips['id'])
            await db.update_status_txn(txn.id, "reject")
    return HTTP_200_OK


@router.post("/{club_id}/general_action_with_user_request", status_code=HTTP_200_OK,
             summary="Подтвердить или отклонить ВСЕ запросы.")
async def v1_general_action_with_user_request(club_id: int, request: Request,
                                              users=Depends(check_rights_user_club_owner)):
    club_owner_account = users[0]
    request = await request.json()
    club = users[2]
    club_balance = club.club_balance
    txn_list = []
    async with DBI() as db:
        for member in await db.get_club_members(club_id):
            txn = await db.get_user_requests_to_replenishment(member.id)
            if txn is None:
                continue
            else:
                txn_list.append(txn)
        sum_all_txn = sum(row.txn_value for row in txn_list)
        if club_balance - sum_all_txn < 0 and request["operation"] == "approve":
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Club balance cannot be less than 0")
        for txn in txn_list:
            if request["operation"] == "approve":
                await db.giving_chips_to_the_user(txn.txn_value, txn.account_id, txn.props["balance"],
                                                  club_owner_account.id)
                await db.update_status_txn(txn.id, "approve")
                await db.refresh_club_balance(club_id, txn.txn_value, "give_out")
            elif request["operation"] == "reject":
                await db.update_status_txn(txn.id, "reject")
            else:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                    detail="Invalid value. Operation must be 'approve' or 'reject")
    return HTTP_200_OK


@router.post("/{club_id}/pick_up_or_give_out_chips", status_code=HTTP_200_OK,
             summary="Pick up or give out chips to members")
async def v1_pick_up_or_give_out_chips(club_id: int, request: Request, users=Depends(check_rights_user_club_owner)):
    mode = (await request.json())['mode']
    members_list = (await request.json())['club_members']
    club_owner_account = users[0]
    club = users[2]
    if len(members_list) == 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Quantity club members for action is invalid')

    amount = (await request.json())['amount']
    if isinstance(amount, str) and amount != 'all':
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid amount value')

    if mode != 'pick_up' and amount != 'all':
        try:
            amount = decimal.Decimal(amount)
            if amount <= 0 or isinstance(amount, decimal.Decimal) is False:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid amount value')
        except decimal.InvalidOperation:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid amount value')

    async with DBI() as db:
        if mode == 'pick_up':
            if amount == "all":
                for member in members_list:
                    if member['balance'] is None and member['balance_shared'] is None:
                        continue
                    elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                        balance_shared = await db.delete_all_chips_from_the_agent_balance(member['id'],
                                                                                          club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance_shared.balance_shared, mode)

                    elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                        balance = await db.delete_all_chips_from_the_account_balance(member['id'],
                                                                                     club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance, mode)
                    elif (member['balance'] or member["balance"] == 0) and (
                            member['balance_shared'] or member["balance_shared"] == 0):
                        balance_shared = await db.delete_all_chips_from_the_agent_balance(member['id'],
                                                                                          club_owner_account.id)
                        balance = await db.delete_all_chips_from_the_account_balance(member['id'],
                                                                                     club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance + balance_shared.balance_shared, mode)
            else:
                amount = round(decimal.Decimal(amount / len(members_list)), 2)
                for member in members_list:
                    if member['balance'] is None and member['balance_shared'] is None:
                        continue
                    elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                        balance_shared = await db.delete_chips_from_the_agent_balance(amount, member['id'],
                                                                                      club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance_shared.balance_shared, mode)
                    elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                        balance = await db.delete_chips_from_the_account_balance(amount, member['id'],
                                                                                 club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance, mode)
                    elif (member['balance'] or member["balance"] == 0) and (
                            member['balance_shared'] or member["balance_shared"] == 0):
                        balance = await db.delete_chips_from_the_account_balance(amount, member['id'],
                                                                                 club_owner_account.id)
                        balance_shared = await db.delete_chips_from_the_agent_balance(amount, member['id'],
                                                                                      club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance + balance_shared.balance_shared, mode)
            return HTTP_200_OK

        elif mode == 'give_out':
            balance_count = 0
            balance_shared_count = 0

            for check_balance in members_list:
                if check_balance['balance'] is None:
                    balance_count = balance_count
                elif check_balance['balance'] >= 0:
                    balance_count += 1
                if check_balance['balance_shared'] is None:
                    balance_shared_count = balance_shared_count
                elif check_balance['balance_shared'] >= 0:
                    balance_shared_count += 1

            if (club.club_balance < amount) or (club.club_balance - amount < 0):
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                    detail='Club balance cannot be less than request amount')
            amount = round(decimal.Decimal(amount / len(members_list)), 2)
            for member in members_list:
                if member['balance'] is None and member['balance_shared'] is None:
                    continue
                elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                    await db.giving_chips_to_the_user(amount, member['id'], "balance_shared", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount, mode)
                elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                    await db.giving_chips_to_the_user(amount, member['id'], "balance", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount, mode)
                elif (member['balance'] or member["balance"] == 0) and (
                        member['balance_shared'] or member["balance_shared"] == 0):
                    await db.giving_chips_to_the_user(amount, member['id'], "balance", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, member['id'], "balance_shared", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount * 2, mode)
            return HTTP_200_OK

        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid mode value')


@router.get("/{club_id}/club_txn_history", status_code=HTTP_200_OK, summary='Get club transaction history')
async def v1_club_txn_history(club_id: int, request: Request, users=Depends(check_rights_user_club_owner_or_manager)):
    async with DBI() as db:
        all_club_members_id = [member.id for member in await db.get_club_members(club_id)]
        if len(all_club_members_id) == 0:
            return []
        result_list = []
        for member_id in all_club_members_id:
            all_member_txns = await db.get_all_account_txn(member_id)  # Возвращает список id транзакций
            recipient = await db.get_club_member(member_id)
            member_user_profile = await db.get_user(recipient.user_id)
            for txn in all_member_txns:
                if txn.txn_type in ["CASHOUT", "BUYIN"]:
                    continue
                try:
                    sender = await db.get_club_member(txn.sender_id)
                    sender_user_profile = await db.get_user(sender.user_id)

                    txn_model = ClubHistoryTransaction(
                        txn_type=txn.txn_type,
                        txn_value=-txn.txn_value,
                        txn_time=txn.created_ts.timestamp(),
                        recipient_id=member_id,
                        recipient_name=member_user_profile.name,
                        recipient_nickname=recipient.nickname,
                        recipient_country=member_user_profile.country,
                        recipient_role=recipient.user_role,
                        sender_id=txn.sender_id,
                        sender_name=sender_user_profile.name,
                        sender_nickname=sender.nickname,
                        sender_country=sender_user_profile.country,
                        sender_role=sender.user_role,
                        balance_type=txn.props.get('balance_type', None)
                    )
                    result_list.append(txn_model)
                except AttributeError as error:
                    # log.info(f"Error getting club. Error: {error}")
                    continue
    return result_list



@router.patch("/{club_id}/set_user_data", status_code=HTTP_200_OK, summary="Set a user nickname and comment")
async def v1_set_user_data(club_id: int, params: ChangeMembersData, users=Depends(check_rights_user_club_owner_or_manager)):
    user_id = params.user_id
    nickname = params.nickname
    club_comment = params.club_comment
    user_role = params.user_role

    async with DBI() as db:
        account = await db.find_account(user_id=params.user_id, club_id=club_id)
        if user_id is None:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail='User id is not specified')
        if club_comment is None and nickname is None:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail='You not specified any params')
        if account is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='No such account was found')
        await db.club_owner_update_user_account(account.id, nickname=nickname, club_comment=club_comment, user_role=user_role)
    return HTTP_200_OK


@router.get("/{club_id}/members/agents", status_code=HTTP_200_OK, summary="Страница возвращающая всех агентов и суперагентов в клубе")
async def v1_club_agents(club_id: int, users=Depends(check_rights_user_club_owner_or_manager)):
    # club_owner_account, user, club
    owner, _, club = users
    """
    ClubMemberProfile(BaseModel):
        id: int | None = None
        username=: str | None = None
        image_id=: int | None = None
        user_role=: str | None = None
        user_approved: bool | None = None
        country=: str | None = None
        nickname=: str | None = None
        balance=: float | None = 00.00
        balance_shared=: float | None = 00.00
    
        join_in_club=: float | None = None
        leave_from_club: float | None = None
    
        user_comment=: str | None = None
    """
    agents_list = []
    async with DBI() as db:
        for agent in await db.club_agents(club.id):
            user = await db.get_user(agent.user_id)
            agent = ClubMemberProfile(
                id=user.id,
                username=user.name,
                image_id=user.image_id,
                user_role=agent.user_role,
                country=user.country,
                nickname=agent.nickname,
                balance=agent.balance,
                balance_shared=agent.balance_shared,
                join_in_club=agent.approved_ts.timestamp()
            )
            agents_list.append(agent)
    return agents_list