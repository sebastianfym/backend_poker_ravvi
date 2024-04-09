import decimal
import time

from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, \
    HTTP_422_UNPROCESSABLE_ENTITY, HTTP_200_OK
from fastapi import Request, HTTPException, Depends
from .utilities import check_rights_user_club_owner_or_manager
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user
from .router import router
from .types import *


@router.get("/{club_id}/members", summary="Получить участников клуба", responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Member not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "Your account has not been verified"}
            })
async def v1_get_club_members(club_id: int, session_uuid: SessionUUID) -> List[ClubMemberProfile]:
    """
    Служит для получения всех участников в клубе

    - **club_id**: number

    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        result_list = []
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        member_account = await db.find_account(user_id=user.id, club_id=club_id)
        if member_account.approved_ts is None:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Your account has not been verified")
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

            statistics_of_all_player_games_in_the_club = await db.statistics_all_games_users_in_club(user.id, club_id)
            hands = len(statistics_of_all_player_games_in_the_club)
            try:
                last_game = await db.get_game_and_players(statistics_of_all_player_games_in_the_club[-1].id)
                last_game_time = last_game[0].begin_ts.timestamp()
            except IndexError:
                last_game_time = None

            winning_row = await db.get_all_account_txns(member.id)

            sum_all_buyin = sum(
                [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'BUYIN']])
            sum_all_cashout = sum(
                [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'CASHOUT']])
            winning = sum_all_cashout - abs(sum_all_buyin)

            member = ClubMemberProfile(
                id=user.id, #member.id,  #
                username=user.name,
                nickname=member.nickname,
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


@router.post("/{club_id}/members", summary="Подтверждает заявку на вступление в клуб", responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Member not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "Your account has not been verified"}
            })
async def v1_join_club(club_id: int, session_uuid: SessionUUID, params: MemberApplicationForMembership) -> ClubProfile:
    """
    Служит для подтверждения заявки участника на вступление в клуб

    - **club_id**: number

    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)

        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        user_comment = params.user_comment
        if not account:
            if club.automatic_confirmation:
                account = await db.create_club_member(club.id, user.id, user_comment, True)
            else:
                account = await db.create_club_member(club.id, user.id, user_comment, False)
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


@router.post("/{club_id}/profile/{user_id}", status_code=HTTP_200_OK,
             summary="Страница с информацией о конкретном участнике клуба для админа",
             responses={
                404: {"model": ErrorException, "detail": "Such a user is not a member of the club",
                      "message": "Such a user is not a member of the club"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "Your account has not been verified"}
            })
async def v1_club_member(club_id: int, user_id: int, session_uuid: SessionUUID, sorting_date: SortingByDate) -> MemberAccountDetailInfo:
    """
    Служит для получения информации о конкретном участнике клуба для админа

    - **club_id**: number

    - **user_id**: number

    """
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

        player_user = await db.get_user(id=user_id)
        opportunity_leave = True
        if account.user_role == "O":
            opportunity_leave = False
        if not account or account.closed_ts is not None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Account not found")

        table_id_list = [table.id for table in await db.get_club_tables(club_id)]

        # Todo сортировка по дате
        if sorting_date.starting_date:
            start_time = datetime.datetime.fromtimestamp(sorting_date.starting_date).strftime('%Y-%m-%d %H:%M:%S')
        else:
            start_time = None

        if sorting_date.end_date:
            end_time = datetime.datetime.fromtimestamp(sorting_date.end_date).strftime('%Y-%m-%d %H:%M:%S')
        else:
            end_time = None

        time_obj = datetime.datetime.fromisoformat(str(account.created_ts))
        unix_time = int(time.mktime(time_obj.timetuple()))
        now_datestamp = int(time.mktime(datetime.datetime.fromisoformat(str(datetime.datetime.utcnow())).timetuple()))

        # date_now = str(datetime.datetime.now()).split(" ")[0]
        table_types = []
        game_types = []
        game_subtype = []
        count_of_games_played = 0

        for table_id in table_id_list:
            # for game in await db.statistics_of_games_played(table_id, date_now):
            if start_time and end_time:
                games = await db.game_statistics_for_a_certain_time(table_id, start_time, end_time)
            else:
                games = await db.get_game_statistics_for_table_and_user(table_id, player_user.id)
                # print(games)
            for game in games:
                # count_of_games_played += 1
                table_types.append((await db.get_table(game.table_id)).table_type)
                game_types.append(game.game_type)
                game_subtype.append(game.game_subtype)

        # winning_row = await db.get_statistics_about_winning(account.id, date_now)
        if start_time and end_time:
            winning_row = await db.get_statistics_about_winning(account.id, start_time, end_time)
        else:
            print(account)
            winning_row = await db.get_all_statistics_about_winning(account.id)
        sum_all_buyin = sum(
            [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'BUYIN']])
        sum_all_cashout = sum(
            [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'REWARD']])
        winning = sum_all_cashout - abs(sum_all_buyin)

        bb_100_winning = 0

        all_games_id = [id.game_id for id in await db.all_players_games(player_user.id)]  # user.id
        access_games = []
        access_game_id = []

        for game_id in all_games_id:
            # game = await db.check_game_by_date(game_id, date_now)
            if start_time and end_time:
                game = await db.check_game_by_date(game_id, start_time, end_time)
            else:
                game = await db.check_game_by_id(game_id)
            if game is not None:
                access_games.append(game)
                access_game_id.append(game.id)

        game_props_list = []
        for game_id in access_game_id:
            balance_data = await db.get_balance_begin_and_end_from_game(game_id, player_user.id)  #
            game_data = await db.get_game_and_players(game_id)
            if balance_data.balance_end:
                balance_end = balance_data.balance_end
            game_props_list.append({'game_id': game_id, 'balance_begin': balance_data.balance_begin,
                                    'balance_end': balance_data.balance_end,
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

        user_profile = await db.get_user(id=user_id)

        statistics_of_all_player_games_in_the_club = await db.statistics_all_games_users_in_club(user.id, club_id)
        hands = len(statistics_of_all_player_games_in_the_club)
        try:
            last_game = await db.get_game_and_players(statistics_of_all_player_games_in_the_club[-1].id)
            last_game_time = last_game[0].begin_ts.timestamp()
        except IndexError:
            last_game_time = None

        if account.user_role not in ["A", "S"]:
            balance_shared = None
        else:
            balance_shared = account.balance_shared

        return MemberAccountDetailInfo(
            id=player_user.id,
            join_datestamp=unix_time,
            now_datestamp=now_datestamp,
            timezone=club.timezone,
            last_game=last_game_time,
            last_session=last_session.created_ts.timestamp(),
            # Todo изменить значение у поля las_entrance_in_club на актуальную последнюю дату входа в клуб
            last_entrance_in_club=last_session.created_ts.timestamp(),
            nickname=account.nickname,
            country=user_profile.country,
            club_comment=account.club_comment,
            user_role=account.user_role,
            username=user.name,
            balance=account.balance,
            balance_shared=balance_shared,
            opportunity_leave=opportunity_leave,
            # hands=count_of_games_played,  # todo потом добавить триггеры
            hands=hands,
            winning=winning,
            bb_100_winning=bb_100
        )


@router.post("/{club_id}/user_account", status_code=HTTP_200_OK, summary="Страница с информацией о конкретном участнике клуба",
             responses={
                404: {"model": ErrorException, "detail": "Club or account not found",
                      "message": "Such a user is not a member of the club"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "Your account has not been verified"}
            })
async def v1_detail_account(club_id: int, session_uuid: SessionUUID) -> AccountDetailInfo:
    """
    Служит для получения профиля игрока в клубе

    - **club_id**: number

    """
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
        # date_now = str(datetime.datetime.now())
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

        winning_row = await db.get_statistics_about_winning_for_today(account.id, date_now)
        sum_all_buyin = sum(
            [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'BUYIN']])
        sum_all_cashout = sum(
            [float(value) for value in [row.txn_value for row in winning_row if row.txn_type == 'REWARD']])
        winning = sum_all_cashout - abs(sum_all_buyin)

        bb_100_winning = 0

        all_games_id = [id.game_id for id in await db.all_players_games(user.id)]  # user.id
        access_games = []
        access_game_id = []

        for game_id in all_games_id:
            game = await db.check_game_by_date(game_id, date_now, date_end=date_now) #Todo подумать над корректным значением для date_end
            if game is not None:
                access_games.append(game)
                access_game_id.append(game.id)

        game_props_list = []
        for game_id in access_game_id:
            balance_data = await db.get_balance_begin_and_end_from_game(game_id, user.id)  #
            print(balance_data)
            game_data = await db.get_game_and_players(game_id)
            if balance_data.balance_end:
                balance_end = balance_data.balance_end
            print("balance_end", balance_data.balance_end)
            game_props_list.append({'game_id': game_id, 'balance_begin': balance_data.balance_begin,
                                    'balance_end': balance_data.balance_end,
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
            winning=round(winning, 2),
            bb_100_winning=bb_100,
            balance=account.balance
        )


@router.patch("/{club_id}/set_user_data", status_code=HTTP_200_OK, summary="Владелец устанавливает ник или комментарий для пользоваателя",
             responses={
                400: {"model": ErrorException, "detail": "User id is not specified",
                      "message": "User id is not specified"},
                404: {"model": ErrorException, "detail": "Club or account not found",
                      "message": "Such a user is not a member of the club"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "Your account has not been verified"},
                422: {"model": ErrorException, "detail": "You not specified any params",
                       "message": "You not specified any params"}
            })
async def v1_set_user_data(club_id: int, params: ChangeMembersData, users=Depends(check_rights_user_club_owner_or_manager)):
    """
    Служит для установки никнейма и/или комментария участнику клуба

    - **club_id**: number

    """
    #Todo добавить типизацию для вывода !
    user_id = params.id
    nickname = params.nickname
    club_comment = params.club_comment
    user_role = params.user_role

    async with DBI() as db:
        account = await db.find_account(user_id=params.id, club_id=club_id)
        if user_id is None:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='User id is not specified')
        if club_comment is None and nickname is None and user_role is None:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail='You not specified any params')
        if account is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail='No such account was found')
        await db.club_owner_update_member_account(account.id, nickname=nickname, club_comment=club_comment, user_role=user_role)
    return HTTP_200_OK



@router.put("/{club_id}/members/{user_id}/agents", status_code=HTTP_200_OK, summary="Установить или убрать агента для пользователя/агента",
                 responses={
                    400: {"model": ErrorException, "detail": "Error with user role"},
                    404: {"model": ErrorException, "detail": "Member, agent or club not found",
                          "message": "Member, agent or club not found"},
                    403: {"model": ErrorException, "detail": "Permission denied",
                          "message": "Your account has not been verified"}
                 })
async def v1_set_user_agent(club_id: int, user_id: int, params: ChangeMembersAgent,
                            users=Depends(check_rights_user_club_owner_or_manager)) -> ClubMemberProfile:
    """
    Служит для назначения или снятия агента с/для пользователя

    - **club_id**: number

    - **user_id**: number

    """
    _, _, _ = users
    async with DBI() as db:
        member = await db.find_account(user_id=user_id, club_id=club_id)
        agent = await db.find_account(user_id=params.agent_id, club_id=club_id)
        if params.agent_id is not None:
            if member is None:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member with this id not found")
            elif agent is None:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Agent with this id not found")
            if member.user_role in ["O", "M"]:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="The owner and manager cannot set up agents")
            if member.user_role == "A" and agent.user_role != "S":
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Only a super agent can be assigned to an agent")
            elif member.user_role == "S" and agent.user_role == "A":
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Only a super agent can be assigned to an super agent")
            await db.update_member_agent(member.id, params.agent_id) #Todo уточнить какой именно мы тут передаем id агента (аккаунта или пользователя)
        else:
            await db.update_member_agent(member.id, None)

        user = await db.get_user(member.user_id)
        return ClubMemberProfile(
                id=member.user_id,
                username=user.name,
                image_id=user.image_id,
                user_role=member.user_role,
                country=user.country,
                nickname=member.nickname,
                balance=member.balance,
                balance_shared=member.balance_shared,
                join_in_club=member.approved_ts.timestamp(),
                agent_id=member.agent_id
            )


@router.get("/{club_id}/members/agents", status_code=HTTP_200_OK,
            responses={
                403: {
                    "model": ErrorException,
                    "detail": "You don't have enough rights to perform this action",
                    "message": "You don't have enough rights to perform this action"
                }
            },
            summary="Страница возвращающая всех агентов и суперагентов в клубе")
async def v1_club_agents(club_id: int, users=Depends(check_rights_user_club_owner_or_manager)) -> Optional[List[ClubAgentProfile]]:
    """
    Возвращает список состоящий из агентов и супер-агентов


    - **id**: id
    - **username**: имя пользователя
    - **image_id**: image_id пользователя
    - **user_role**: роль пользователя в клубе
    - **country**: страна пользователя
    - **nickname**: никнейм игрока внутри самого клуба
    - **agent_id**: id агента к которому привязан пользователь
    - **agents_count**: количество агентов которые привязаны к пользователю
    - **super_agents_count**: количество супер-агентов которые привязаны к пользователю
    - **players**: количество игроков которые привязаны к пользователю

    """
    owner, _, club = users
    agents_list = []
    async with DBI() as db:
        for member in await db.club_agents(club_id):
            user = await db.get_user(member.user_id)
            s_agents_under_agent, agents_under_agent, players_under_agent = await db.members_under_agent(club_id, member.user_id)

            if member.user_role != "S":
                s_agents_under_agent = None
            else:
                s_agents_under_agent = len(s_agents_under_agent)

            agent = ClubAgentProfile(
                id=user.id,
                username=user.name,
                image_id=user.image_id,
                user_role=member.user_role,
                country=user.country,
                nickname=member.nickname,
                agent_id=member.agent_id,
                agents_count=len(agents_under_agent),
                super_agents_count=s_agents_under_agent,
                players=len(players_under_agent)
            )
            agents_list.append(agent)
    return agents_list
