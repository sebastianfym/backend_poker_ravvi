import datetime
from time import timezone
import time

from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_418_IM_A_TEAPOT
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from pydantic import BaseModel

from ..db import DBI
from .utils import SessionUUID, get_session_and_user
from .tables import TableParams, TableProfile

router = APIRouter(prefix="/clubs", tags=["clubs"])


class ClubProps(BaseModel):
    name: str | None = None
    description: str | None = None
    # TODO не должно быть None
    image_id: int | None = None


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


class ClubMemberProfile(BaseModel):
    id: int | None = None
    username: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool | None = None


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


@router.post("", status_code=HTTP_201_CREATED, summary="Create new club")
async def v1_create_club(params: ClubProps, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.create_club(user_id=user.id, name=params.name, description=params.description,
                                    image_id=params.image_id)

    club_profile = ClubProfile(
        id=club.id,
        name=club.name,
        description=club.description,
        image_id=club.image_id,
        user_role="O",
        user_approved=True
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
        # TODO а если клуб закрыт?
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
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
            service_balance=await db.get_service_balance_in_club(club_id=club.id, user_id=user.id)
        )


@router.patch("/{club_id}", summary="Update club")
async def v1_update_club(club_id: int, params: ClubProps, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        # TODO а если клуб закрыт?
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
        # TODO а если клуб закрыт?
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        members = await db.get_club_members(club_id=club.id)

    return list([
        ClubMemberProfile(
            id=member.id,
            # username=member.username,
            # image_id=member.image_id,
            user_role=member.user_role,
            # TODO наверное исключенных игроков не надо показывать?
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
        elif account.closed_ts is not None and account.club_id == club_id:
            await db.return_member_in_club(account.id)

    return ClubProfile(
        id=club.id,
        name=club.name,
        description=club.description,
        user_role=account.user_role,
        # TODO а зачем? тут всегда True
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
        if not member or member.club_id != club.id:
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

        table_type = kwargs.get('table_type')  # .value
        table_name = kwargs.get('table_name')
        table_seats = kwargs.get('table_seats')
        game_type = kwargs.get('game_type')  # .value
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
async def v1_add_chip_on_club_balance(club_id: int, session_uuid: SessionUUID, request: Request):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        elif club.closed_ts:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)

        if account.user_role != "O":
            return HTTPException(status_code=HTTP_403_FORBIDDEN,
                                 detail="You don't have enough rights to perform this action")

        json_data = await request.json()
        try:
            amount = json_data["amount"]
            if isinstance(amount, float) is False or amount < 0:
                return HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                     detail="You entered an incorrect value for amount")
            amount = round(amount, 2)
            await db.txn_with_chip_on_club_balance(club_id, amount, "add")
            return HTTP_200_OK
        except KeyError:
            return HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="You forgot to amount out quantity the chips")


@router.post("/{club_id}/delete_chip_from_club_balance", status_code=HTTP_200_OK,
             summary="Take away a certain number of chips from the club's balance")
async def v1_delete_chip_from_club_balance(club_id: int, session_uuid: SessionUUID, request: Request):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        try:
            if account.user_role != "O":
                return HTTPException(status_code=HTTP_403_FORBIDDEN,
                                     detail="You don't have enough rights to perform this action")
        except AttributeError:
            return HTTPException(status_code=HTTP_403_FORBIDDEN,
                                 detail="You don't have enough rights to perform this action")

        json_data = await request.json()
        try:
            amount = json_data["amount"]
            await db.txn_with_chip_on_club_balance(club_id, amount, "del")
            return HTTP_200_OK
        except KeyError as e:
            return HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"You forgot to add a value: {e}")


@router.post("/{club_id}/giving_chips_to_the_user", status_code=HTTP_200_OK,
             summary="Owner giv chips to the club's user")
async def v1_club_giving_chips_to_the_user(club_id: int, session_uuid: SessionUUID, request: Request):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        try:
            if account.user_role != "O":
                return HTTPException(status_code=HTTP_403_FORBIDDEN,
                                     detail="You don't have enough rights to perform this action")
        except AttributeError:
            return HTTPException(status_code=HTTP_403_FORBIDDEN,
                                 detail="You don't have enough rights to perform this action")
        json_data = await request.json()

        try:
            amount = json_data["amount"]
            balance = json_data["balance"]

            if isinstance(amount, float) is False or amount < 0:
                return HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                     detail="You entered an incorrect value for amount")
            if balance != "balance" or balance != "balance_shared":
                return HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                     detail="You entered an incorrect value for balance")
            user_account_id = json_data["user_id"]
            user_account = await db.find_account(user_id=user_account_id, club_id=club_id)
            if user_account.user_role == "P":
                balance = "balance"

            await db.giving_chips_to_the_user(amount, user_account.id, balance)
            return HTTP_200_OK

        except KeyError as e:
            return HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"You forgot to add a value: {e}")


@router.post("/{club_id}/delete_chips_from_the_user", status_code=HTTP_200_OK,
             summary="Owner take away chips from the club's user")
async def v1_club_delete_chips_from_the_user(club_id: int, session_uuid: SessionUUID, request: Request):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        try:
            if account.user_role != "O":
                return HTTPException(status_code=HTTP_403_FORBIDDEN,
                                     detail="You don't have enough rights to perform this action")
        except AttributeError:
            return HTTPException(status_code=HTTP_403_FORBIDDEN,
                                 detail="You don't have enough rights to perform this action")

        json_data = await request.json()

        try:
            amount = json_data["amount"]
            user_account_id = json_data["user_id"]
            balance = json_data["balance"]
            user_account = await db.find_account(user_id=user_account_id, club_id=club_id)
            if balance == "balance":
                await db.delete_chips_from_the_account_balance(amount, user_account.id)
            elif balance == "balance_shared":
                await db.delete_chips_from_the_agent_balance(amount, user_account.id)
            return HTTP_200_OK
        except KeyError as e:
            return HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"You forgot to add a value: {e}")


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
                return HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Your account has not been verified")
        except AttributeError:
            return HTTPException(status_code=HTTP_403_FORBIDDEN,
                                 detail="You don't have enough rights to perform this action")

        json_data = await request.json()

        try:
            amount = json_data["amount"]
            balance = json_data["balance"]
        except KeyError as e:
            return HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"You forgot to add a value: {e}")

        if account.user_role == "P":
            balance = "balance"

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
        await db.leave_from_club(account.id)
        return HTTP_200_OK


@router.get("/{club_id}/user_account", status_code=HTTP_200_OK, summary="Page with data about user's account in club")
async def v1_user_account(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")

        account = await db.find_account(user_id=user.id, club_id=club_id)
        # print(account.id) #1005
        opportunity_leave = True
        if account.user_role == "O":
            opportunity_leave = False
        if not account or account.closed_ts is not None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Account not found")

        table_id_list = [table.id for table in await db.get_club_tables(club_id)]
        # game_id_list = [game_id.game_id for game_id in await db.all_players_games(user.id)]
        # table_params_list = [{"id": table.id, "table_type": table.table_type, "game_type": table.game_type, "game_subtype": table.game_subtype}
        #                      for table in await db.get_club_tables(club_id)]

        time_obj = datetime.datetime.fromisoformat(str(account.created_ts))
        unix_time = int(time.mktime(time_obj.timetuple()))

        now_datestamp = int(time.mktime(datetime.datetime.fromisoformat(str(datetime.datetime.utcnow())).timetuple()))

        date_now = str(datetime.datetime.now()).split(" ")[0]
        """ (эти операции должны быть на 1ом столе)
        buyin - взял фишки на стол
        -
        -
        -
        -
        CASHOUT - уход со стола с оставшимися фишками или нулем
        
        winning =  получить все cashout и все buyin со стола , сложить их между друг другом и отнять от sum_all_cashout - sum_all_buyin
        
        бб100 = ((выигрышь разделить на большой блайнд (с профиля игры в пропсах)) // количество игр) и умножить на 100
        Если игра не имеет значения у end_ts, то ее не считаем

        """
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

        winning_row = await db.get_statistics_about_winning(1002, date_now) #account.id Todo замени статичный id на account.id
        sum_all_buyin = sum([float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'BUYIN']])
        sum_all_cashout = sum([float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'CASHOUT']])
        winning = sum_all_cashout - abs(sum_all_buyin)

        bb_100_winning = None
        #С одним значением buyin и cashout

        return AccountDetailInfo(
            join_datestamp=unix_time,
            now_datestamp=now_datestamp,
            timezone="Asia/Singapore",
            table_types=set(table_types),
            game_types=set(game_types),
            game_subtypes=set(game_subtype),
            opportunity_leave=opportunity_leave,
            hands=count_of_games_played, #todo потом добавить триггеры
            winning=winning,
            bb_100_winning=bb_100_winning #TODO как это считать ?
        )
