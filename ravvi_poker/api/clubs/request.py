from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_200_OK
from fastapi import Request, HTTPException, Depends
from .utilities import check_rights_user_club_owner_or_manager, check_rights_user_club_owner
from ...db import DBI
from .router import router
from .types import *


@router.put("/{club_id}/members/{user_id}", summary="Принимает заявку на вступление в клуб",
            responses={
                404: {"model": ErrorException, "detail": "Club or member not found",
                      "message": "Club or member not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions for that action"},
                400:  {"model": ErrorException, "detail": "An unexpected error has occurred",
                       "message": "An unexpected error has occurred"}
            },
            )
async def v1_approve_join_request(club_id: int, user_id: int, params: UserRequestsToJoin,
                                  users=Depends(check_rights_user_club_owner)) -> ClubMemberProfile:
    """
    Служит для подтверждения заявки участника на вступление в клуб

    - **club_id**: number

    """
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


@router.delete("/{club_id}/members/{user_id}", status_code=HTTP_200_OK, summary="Отклоняет заявку на вступление в клуб",
            responses={
                404: {"model": ErrorException, "detail": "Club or member not found",
                      "message": "Club or member not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions for that action"}
            },
            )
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


@router.get("/{club_id}/members/requests", status_code=HTTP_200_OK,summary="Отображение всех заявок на вступление в клуб",
            responses={
                404: {"model": ErrorException, "detail": "Member not found",
                      "message": "Member not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions for that action"}
            }
            )
async def v1_requests_to_join_in_club(club_id: int, users=Depends(check_rights_user_club_owner)) -> List[ClubMemberProfile]:
    """
    Служит для отображения заявок участников на вступление в клуб

    - **club_id**: number

    """
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
