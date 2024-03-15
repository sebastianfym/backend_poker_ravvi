import datetime
from decimal import Decimal
from datetime import datetime as DateTime
from fastapi import HTTPException, Depends
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_400_BAD_REQUEST
from pydantic import BaseModel, Field, field_validator, validator

from ..clubs import check_rights_user_club_owner
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user
# from ..types import HTTPError
from .types import ChipsRequestParams, ChipsRequestItem, UserRequest, ChipRequestForm, ErrorException

from .router import router


# CREATE CHIPS REQUEST

@router.post("/{club_id}/requests/chips", status_code=HTTP_201_CREATED,
             responses={
                 400: {"model": ErrorException, "description": "Your request is still under consideration"},
                 403: {"model": ErrorException, "description": "You don't have enough permissions"},
                 404: {"model": ErrorException, "description": "Club or member not found"},
             },
             summary="Отправить запрос на пополнение баланса")
async def v1_chips_requests_post(club_id: int, params: ChipsRequestParams,
                                 session_uuid: SessionUUID) -> ChipsRequestItem:
    """
    Отправляет запрос от лица пользователя в адрес клуба на пополнение баланса.

    - **amount**: number >= 1
    - **agent**: number
    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(club_id=club_id, user_id=user.id)

        if not account:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Member not found")

        created_ts = DateTime.utcnow().replace(microsecond=0).timestamp()

        try:
            if account.approved_ts is None or account.approved_ts is False:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Your account has not been verified")
        except AttributeError as e:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail=f"{e}")

        check_last_request = await db.check_request_to_replenishment(account.id)

        try:
            if check_last_request.props['status'] == 'consider':
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                    detail="Your request is still under consideration")
        except AttributeError:
            pass

        try:
            amount = params.amount
            agent = params.agent
        except KeyError as e:
            return HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"You forgot to add a value: {e}")
        if agent:
            balance = "balance_shared"
        else:
            balance = "balance"
        if account.user_role not in ["A", "S"] and balance == "balance_shared":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You don't have enough permissions to work "
                                                                       "with agent balance")

        row = await db.send_request_for_replenishment_of_chips(account_id=account.id, amount=amount, balance=balance)

    return ChipsRequestItem(
                id=row.id,
                created_ts=created_ts,
                created_by=user.id,
                txn_type=row.txn_type,
                amount=row.txn_value
                            )


# GET CHIPS REQUESTS

@router.get("/{club_id}/requests/chips", status_code=HTTP_200_OK,
            # responses={
            #     403: {"model": HTTPError, "description": "No access for requested operation"},
            #     404: {"model": HTTPError, "description": "Club not found"},
            # },
            summary="Get open chips requests")
async def v1_chips_requests_get(club_id: int, users=Depends(check_rights_user_club_owner)) -> dict:
    """
    Страница служит для получения всех запросов от пользователей на пополнение баланса

    - **id**: number,

    - **txn_id**: number,

    - **username**: string,

    - **image_id**: number | null,

    - **user_role**: string,

    - **nickname**: string | null,

    - **txn_value**: number >= 1,

    - **txn_type**: string,

    - **balance_type**: string, ["balance_shared" | "balance"]

    - **join_in_club**: timestamp,

    - **leave_from_club**: timestamp | null,

    - **country**: string | null

    """
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
                        id=user.id,  # member.id,
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
    # return []


# APPROVE CHIPS REQUEST

@router.put("/{club_id}/requests/chips/{request_id}", status_code=HTTP_200_OK,
            responses={
                400: {"model": ErrorException, "detail": "Club balance cannot be less than 0"},
                403: {"model": ErrorException, "description": "No access for requested operation"},
                404: {"model": ErrorException, "detail": "Club not found"},
            },
            summary="Подтвердить заявку на пополнение баланса")
async def v1_chips_requests_put(club_id: int, request_id: int, users=Depends(check_rights_user_club_owner)): #-> ChipsRequestItem:
    """
    Подтверждает запрос на пополнение баланса клуба
    """
    club_owner_account, user, club = users
    club_balance = club.club_balance
    async with DBI() as db:
        txn = await db.get_specific_txn(request_id)
        if club_balance - txn.txn_value < 0:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Club balance cannot be less than 0')
        await db.giving_chips_to_the_user(txn.txn_value, txn.account_id, txn.props["balance"], user.id)
                                          # club_owner_account.id)

        txn = await db.update_status_txn(txn.id, "approve")
        await db.refresh_club_balance(club_id, txn.txn_value, "give_out")
    return ChipsRequestItem(
                id=txn.id,
                created_ts=txn.created_ts.utcnow().replace(microsecond=0).timestamp(),
                created_by=txn.account_id,
                txn_type=txn.txn_type,
                amount=txn.txn_value,
                            )


@router.post("/{club_id}/requests/chips/all", status_code=HTTP_200_OK,
            responses={
                400: {"model": ErrorException, "detail": "Club balance cannot be less than 0"},
                403: {"model": ErrorException, "description": "No access for requested operation"},
                404: {"model": ErrorException, "detail": "Club not found"},
                409: {"model": ErrorException, "detail": "Invalid mode value",
                      "message": "Invalid value. Operation must be 'approve' or 'reject"}

            },
            summary="Подтвердить или отклонить ВСЕ запросы")
async def v1_accept_all_chips_requests(club_id: int, params: ChipRequestForm, users=Depends(check_rights_user_club_owner)):
    """
    Служит для обработки ВСЕХ запросов на пополнение баланса от пользователей

    - **operation**: string ["approve", "reject"]

    """
    club_owner_account, user, club = users
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
        if club_balance - sum_all_txn < 0 and params.operation == "approve":
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Club balance cannot be less than 0")
        for txn in txn_list:
            if params.operation == "approve":
                await db.giving_chips_to_the_user(txn.txn_value, txn.account_id, txn.props["balance"], user.id)
                                                  # club_owner_account.id)
                await db.update_status_txn(txn.id, "approve")
                await db.refresh_club_balance(club_id, txn.txn_value, "give_out")
            elif params.operation == "reject":
                await db.update_status_txn(txn.id, "reject")
            else:
                raise HTTPException(status_code=HTTP_409_CONFLICT,
                                    detail="Invalid value. Operation must be 'approve' or 'reject")
    return HTTP_200_OK
# REJECT CHIPS REQUEST


@router.delete("/{club_id}/requests/chips/{request_id}", status_code=HTTP_200_OK,
               responses={
                   403: {"model": ErrorException, "description": "No access for requested operation"},
                   404: {"model": ErrorException, "description": "Club not found"},
               },
               summary="Отклонить заявку на пополнение баланса")
async def v1_chips_requests_delete(club_id: int, request_id: int, users=Depends(check_rights_user_club_owner)):# -> ChipsRequestItem:
    """
    Ожидаемое тело запроса:

    {    }

    Возвращает status code = 200
    """
    _, _, _ = users
    async with DBI() as db:
        txn = await db.get_specific_txn(request_id)
        await db.update_status_txn(txn.id, "reject")
    return ChipsRequestItem(
        id=txn.id,
        created_ts=txn.created_ts.utcnow().replace(microsecond=0).timestamp(),
        created_by=txn.account_id,
        txn_type=txn.txn_type,
        amount=txn.txn_value,
    )

