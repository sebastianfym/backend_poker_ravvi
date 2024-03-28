# import logging
# from uuid import UUID
#
# from fastapi import APIRouter, Request
# from fastapi.exceptions import HTTPException
# from pydantic import BaseModel, EmailStr
# from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_400_BAD_REQUEST
#
# from ..db import DBI as DBI
# from .utils import SessionUUID, get_session_and_user, get_country_code, check_username, check_email
# from .types import UserPublicProfile, UserPrivateProfile, UserMutableProps


# log = logging.getLogger(__name__)
#
# router = APIRouter(prefix="/user", tags=["user"])
#
#
# class UserEmail(BaseModel):
#     email: EmailStr
#
# class UserTempEmail(BaseModel):
#     user_id: int
#     uuid: UUID
#     temp_email: str
#     is_active: bool


# @router.get("/profile", summary="Get user private profile")
# async def v1_get_user_private(session_uuid: SessionUUID):
#     """Get user private profile"""
#     async with DBI() as db:
#         _, user = await get_session_and_user(db, session_uuid)
#
#     return UserPrivateProfile.from_row(user)


# @router.patch("/profile", summary="Update user profile")
# async def v1_update_user(props: UserMutableProps, session_uuid: SessionUUID, request: Request):
#     """Update user profile"""
#     async with DBI() as db:
#         _, user = await get_session_and_user(db, session_uuid)
#         kwargs = props.model_dump(exclude_unset=True)
#         if "country" in kwargs.keys():
#             kwargs['country'] = get_country_code(kwargs['country'])
#         if "name" in kwargs.keys():
#             name = kwargs['name']
#             if await db.check_uniq_username(name) is not None:
#                 raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This name is already taken")
#             check_username(name, user.id)
#         if "email" in kwargs.keys():
#             email = kwargs['email']
#             if await db.check_uniq_email(email) is not None:
#                 raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This email is already taken")
#             check_email(email)
#         user = await db.update_user(user.id, **kwargs)
#     return UserPrivateProfile.from_row(user)


# @router.get("/{user_id}", summary="Get user public info")
# async def v1_get_user_public(user_id: int, session_uuid: SessionUUID):
#     """Get user public info"""
#     async with DBI() as db:
#         await get_session_and_user(db, session_uuid)
#         user = await db.get_user(user_id)
#     if not user:
#         raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
#
#     return UserPublicProfile.from_row(user)
