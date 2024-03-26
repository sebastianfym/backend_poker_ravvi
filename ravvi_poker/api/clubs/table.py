from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, \
    HTTP_422_UNPROCESSABLE_ENTITY, HTTP_200_OK
from fastapi import Request, HTTPException
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user, check_club_name
from .router import router
from .types import *


@router.post("/{club_id}/tables", status_code=HTTP_201_CREATED, summary="Create club table",
             responses={
                 404: {"model": ErrorException, "detail": "Club not found",
                       "message": "Club not found"},
                 403: {"model": ErrorException, "detail": "Permission denied",
                       "message": "You dont have permissions for that action"},
                 400: {"model": ErrorException, "detail": "Invalid parameters",
                       "message": "Invalid parameters"}
             }
             )
async def v1_create_club_table(club_id: int, params: TableParams, session_uuid: SessionUUID, request: Request) -> TableProfile:
    """
    Служит для подтверждения заявки участника на вступление в клуб

    - **club_id**: number

    """
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


@router.get("/{club_id}/tables", status_code=HTTP_200_OK, summary="Get club tables",
            responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Member not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions for that action"}
            }
            )
async def v1_get_club_tables(club_id: int, session_uuid: SessionUUID) -> List[TableProfile]:
    """
    Служит для получения клубных столов

    - **club_id**: number

    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        account = await db.find_account(user_id=user.id, club_id=club_id)
        if not account:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        if account.approved_ts is None:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Your account has not been verified")
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


@router.get("/{table_id}/result", status_code=200, summary="Get table (SNG/MTT) result",
            responses={
                404: {"model": ErrorException, "detail": "Table not found",
                      "message": "Table not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions for that action"}
            }
            )
async def v1_get_table_result(table_id: int, session_uuid: SessionUUID):
    """
    Служит для получения результатов на конкретном столе

    - **table_id**: number

    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        table = await db.get_table(table_id)
        if not table:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        if table.table_type not in ('SNG', 'MTT'):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        rows = await db.get_table_result(table_id)
        rows.sort(key=lambda x: x.balance_end or x.balance_begin or 0, reverse=True)
        result = []
        for i, r in enumerate(rows, start=1):
            res = dict(
                user_id=r.user_id,
                username=r.username,
                image_id=r.image_id,
                reward=r.balance_end,
                rank=i
            )
            result.append(res)
    return dict(result=result)