import datetime
import decimal
from typing import Annotated

from fastapi import Depends, Request, HTTPException
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from .router import router
from .types import UserChipsValue, ClubChipsValue, UserRequest, ChipRequestForm
from .utilities import check_compatibility_recipient_and_balance_type, check_rights_user_club_owner
from ..utils import SessionUUID, get_session_and_user
from ...db import DBI


@router.post("/{club_id}/giving_chips_to_the_user", status_code=HTTP_200_OK,
             summary="Owner giv chips to the club's user")
async def v1_club_giving_chips_to_the_user(club_id: int, request: Annotated[
    UserChipsValue, Depends(check_compatibility_recipient_and_balance_type)],
                                           users=Depends(check_rights_user_club_owner)):
    async with DBI() as db:
        member = await db.find_account(user_id=request.account_id, club_id=club_id)
        # await db.giving_chips_to_the_user(request.amount, request.account_id, request.balance, users[0].id)
        await db.giving_chips_to_the_user(request.amount, member.id, request.balance, users[0].id)


@router.post("/{club_id}/delete_chips_from_the_user", status_code=HTTP_200_OK,
             summary="Owner take away chips from the club's user")
async def v1_club_delete_chips_from_the_user(club_id: int, request: Annotated[
    UserChipsValue, Depends(check_compatibility_recipient_and_balance_type)],
                                             users=Depends(check_rights_user_club_owner)):
    async with DBI() as db:
        member = await db.find_account(user_id=request.account_id, club_id=club_id)
        if request.balance == "balance":
            # await db.delete_chips_from_the_account_balance(request.amount, request.account_id, users[0].id)
            await db.delete_chips_from_the_account_balance(request.amount, member.id, users[0].id)
        else:
            # await db.delete_chips_from_the_agent_balance(request.amount, request.account_id, users[0].id)
            await db.delete_chips_from_the_agent_balance(request.amount, member.id, users[0].id)


@router.post("/{club_id}/request_chips", status_code=HTTP_200_OK, summary="Пользователь запрашивает фишки у клуба")
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


@router.post("/{club_id}/add_chip_on_club_balance", status_code=HTTP_200_OK,
             summary="Adds a certain number of chips to the club's balance")
async def v1_add_chip_on_club_balance(club_id: int, chips_value: ClubChipsValue,
                                      users=Depends(check_rights_user_club_owner)):
    club_owner_account, user, _ = users
    async with DBI() as db:
        await db.txn_with_chip_on_club_balance(club_id, chips_value.amount, "CHIPSIN", club_owner_account.id, user.id)


@router.post("/{club_id}/delete_chip_from_club_balance", status_code=HTTP_200_OK,
             summary="Take away a certain number of chips from the club's balance")
async def v1_delete_chip_from_club_balance(club_id: int, chips_value: ClubChipsValue,
                                           users=Depends(check_rights_user_club_owner)):
    club_owner_account, user = users[0], users[1]
    async with DBI() as db:
        await db.txn_with_chip_on_club_balance(club_id, chips_value.amount, "CHIPSOUT", club_owner_account.id, user.id)


@router.post("/{club_id}/giving_chips_to_the_user", status_code=HTTP_200_OK,
             summary="Owner giv chips to the club's user")
async def v1_club_giving_chips_to_the_user(club_id: int, request: Annotated[
    UserChipsValue, Depends(check_compatibility_recipient_and_balance_type)],
                                           users=Depends(check_rights_user_club_owner)):
    async with DBI() as db:
        member = await db.find_account(user_id=request.account_id, club_id=club_id)
        # await db.giving_chips_to_the_user(request.amount, request.account_id, request.balance, users[0].id)
        await db.giving_chips_to_the_user(request.amount, member.id, request.balance, users[0].id)


@router.post("/{club_id}/delete_chips_from_the_user", status_code=HTTP_200_OK,
             summary="Owner take away chips from the club's user")
async def v1_club_delete_chips_from_the_user(club_id: int, request: Annotated[
    UserChipsValue, Depends(check_compatibility_recipient_and_balance_type)],
                                             users=Depends(check_rights_user_club_owner)):
    async with DBI() as db:
        member = await db.find_account(user_id=request.account_id, club_id=club_id)
        if request.balance == "balance":
            await db.delete_chips_from_the_account_balance(request.amount, member.id, users[0].id)
        else:
            await db.delete_chips_from_the_agent_balance(request.amount, member.id, users[0].id)


@router.post("/{club_id}/request_chips", status_code=HTTP_200_OK, summary="Пользователь запрашивает фишки у клуба")
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
                        id=user.id, #member.id,
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
                    account = await db.find_account(user_id=member['id'], club_id=club_id)
                    if member['balance'] is None and member['balance_shared'] is None:
                        continue
                    elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                        # balance_shared = await db.delete_all_chips_from_the_agent_balance(member['id'], club_owner_account.id)
                        balance_shared = await db.delete_all_chips_from_the_agent_balance(account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance_shared.balance_shared, mode)

                    elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                        # balance = await db.delete_all_chips_from_the_account_balance(member['id'], club_owner_account.id)
                        balance = await db.delete_all_chips_from_the_account_balance(account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance, mode)

                    elif (member['balance'] or member["balance"] == 0) and (
                            member['balance_shared'] or member["balance_shared"] == 0):
                        # balance_shared = await db.delete_all_chips_from_the_agent_balance(member['id'],club_owner_account.id)
                        # balance = await db.delete_all_chips_from_the_account_balance(member['id'],club_owner_account.id)
                        balance_shared = await db.delete_all_chips_from_the_agent_balance(account.id,club_owner_account.id)
                        balance = await db.delete_all_chips_from_the_account_balance(account.id,club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance + balance_shared.balance_shared, mode)
            else:
                amount = round(decimal.Decimal(amount / len(members_list)), 2)
                for member in members_list:
                    account = await db.find_account(user_id=member['id'], club_id=club_id)
                    if member['balance'] is None and member['balance_shared'] is None:
                        continue
                    elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                        # balance_shared = await db.delete_chips_from_the_agent_balance(amount, member['id'],club_owner_account.id)
                        balance_shared = await db.delete_chips_from_the_agent_balance(amount, account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance_shared[0].balance_shared, mode)

                    elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                        # balance = await db.delete_chips_from_the_account_balance(amount, member['id'], club_owner_account.id)
                        balance = await db.delete_chips_from_the_account_balance(amount, account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance, mode)

                    elif (member['balance'] or member["balance"] == 0) and (member['balance_shared'] or member["balance_shared"] == 0):
                        # balance = await db.delete_chips_from_the_account_balance(amount, member['id'],club_owner_account.id)
                        # balance_shared = await db.delete_chips_from_the_agent_balance(amount, member['id'],club_owner_account.id)
                        balance = await db.delete_chips_from_the_account_balance(amount, account.id, club_owner_account.id)
                        balance_shared = await db.delete_chips_from_the_agent_balance(amount, account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance + balance_shared[0].balance_shared, mode)
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
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Club balance cannot be less than request amount')
            amount = round(decimal.Decimal(amount / len(members_list)), 2)
            for member in members_list:
                account = await db.find_account(user_id=member['id'], club_id=club_id)
                if member['balance'] is None and member['balance_shared'] is None:
                    continue
                elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                    # await db.giving_chips_to_the_user(amount, member['id'], "balance_shared", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance_shared", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount, mode)
                elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                    # await db.giving_chips_to_the_user(amount, member['id'], "balance", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount, mode)
                elif (member['balance'] or member["balance"] == 0) and (member['balance_shared'] or member["balance_shared"] == 0):
                    # await db.giving_chips_to_the_user(amount, member['id'], "balance", club_owner_account.id)
                    # await db.giving_chips_to_the_user(amount, member['id'], "balance_shared", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance_shared", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount * 2, mode)
            return HTTP_200_OK

        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid mode value')


@router.post("/{club_id}/action_with_user_request", status_code=HTTP_200_OK,
             summary='Подтвердить или отклонить пользовательские запросы на пополнение баланса')
async def v1_action_with_user_request(club_id: int, request_for_chips: ChipRequestForm, users=Depends(check_rights_user_club_owner)):
    club_owner_account = users[0]
    club = users[2]
    club_balance = club.club_balance
    request_for_chips = request_for_chips.model_dump()
    async with DBI() as db:
        if request_for_chips["operation"] == "approve":
            txn = await db.get_specific_txn(request_for_chips['id'])
            if club_balance - txn.txn_value < 0:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Club balance cannot be less than 0')
            # member = await db.find_account(user_id=txn.account_id, club_id=club_id)
            await db.giving_chips_to_the_user(txn.txn_value, txn.account_id, txn.props["balance"], club_owner_account.id)
            # await db.giving_chips_to_the_user(txn.txn_value, member.id, txn.props["balance"], club_owner_account.id)

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
                    account = await db.find_account(user_id=member['id'], club_id=club_id)
                    if member['balance'] is None and member['balance_shared'] is None:
                        continue
                    elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                        # balance_shared = await db.delete_all_chips_from_the_agent_balance(member['id'], club_owner_account.id)
                        balance_shared = await db.delete_all_chips_from_the_agent_balance(account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance_shared.balance_shared, mode)

                    elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                        # balance = await db.delete_all_chips_from_the_account_balance(member['id'], club_owner_account.id)
                        balance = await db.delete_all_chips_from_the_account_balance(account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance, mode)

                    elif (member['balance'] or member["balance"] == 0) and (
                            member['balance_shared'] or member["balance_shared"] == 0):
                        # balance_shared = await db.delete_all_chips_from_the_agent_balance(member['id'],club_owner_account.id)
                        # balance = await db.delete_all_chips_from_the_account_balance(member['id'],club_owner_account.id)
                        balance_shared = await db.delete_all_chips_from_the_agent_balance(account.id,club_owner_account.id)
                        balance = await db.delete_all_chips_from_the_account_balance(account.id,club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance + balance_shared.balance_shared, mode)
            else:
                amount = round(decimal.Decimal(amount / len(members_list)), 2)
                for member in members_list:
                    account = await db.find_account(user_id=member['id'], club_id=club_id)
                    if member['balance'] is None and member['balance_shared'] is None:
                        continue
                    elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                        # balance_shared = await db.delete_chips_from_the_agent_balance(amount, member['id'],club_owner_account.id)
                        balance_shared = await db.delete_chips_from_the_agent_balance(amount, account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance_shared[0].balance_shared, mode)

                    elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                        # balance = await db.delete_chips_from_the_account_balance(amount, member['id'], club_owner_account.id)
                        balance = await db.delete_chips_from_the_account_balance(amount, account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance, mode)

                    elif (member['balance'] or member["balance"] == 0) and (member['balance_shared'] or member["balance_shared"] == 0):
                        # balance = await db.delete_chips_from_the_account_balance(amount, member['id'],club_owner_account.id)
                        # balance_shared = await db.delete_chips_from_the_agent_balance(amount, member['id'],club_owner_account.id)
                        balance = await db.delete_chips_from_the_account_balance(amount, account.id, club_owner_account.id)
                        balance_shared = await db.delete_chips_from_the_agent_balance(amount, account.id, club_owner_account.id)
                        await db.refresh_club_balance(club_id, balance.balance + balance_shared[0].balance_shared, mode)
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
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Club balance cannot be less than request amount')
            amount = round(decimal.Decimal(amount / len(members_list)), 2)
            for member in members_list:
                account = await db.find_account(user_id=member['id'], club_id=club_id)
                if member['balance'] is None and member['balance_shared'] is None:
                    continue
                elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                    # await db.giving_chips_to_the_user(amount, member['id'], "balance_shared", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance_shared", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount, mode)
                elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                    # await db.giving_chips_to_the_user(amount, member['id'], "balance", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount, mode)
                elif (member['balance'] or member["balance"] == 0) and (member['balance_shared'] or member["balance_shared"] == 0):
                    # await db.giving_chips_to_the_user(amount, member['id'], "balance", club_owner_account.id)
                    # await db.giving_chips_to_the_user(amount, member['id'], "balance_shared", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance", club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance_shared", club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount * 2, mode)
            return HTTP_200_OK

        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid mode value')

