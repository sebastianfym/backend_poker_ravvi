from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

router = APIRouter(prefix="/images", tags=["images"])


class Image(BaseModel):
    id: int
    is_owner: bool


class ImageList(BaseModel):
    images: list[Image]


class ImageUpload(BaseModel):
    image_data: str


@router.get("", summary="Get available images")
async def v1_get_available_images(session_uuid: RequireSessionUUID):
    """Get available images"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        images = dbi.get_user_images(user.id)

    return ImageList(images=[
        Image(
            id=image.id,
            is_owner=(image.owner_id==user.id)
        ) for image in images
    ])


@router.post("", summary="Upload image")
async def v1_upload_image(params: ImageUpload, session_uuid: RequireSessionUUID):
    """Upload image"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        image = dbi.get_user_images(user.id, image_data=params.image_data)
        if not image:
            image = dbi.create_user_image(user.id, params.image_data)

    return Image(
        id=image.id,
        is_owner=(image.owner_id==user.id)
    )


@router.get("/{image_id}", summary="Get image by id")
async def v1_get_image(image_id: int, session_uuid: RequireSessionUUID):
    """Get image by id"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        image = dbi.get_user_images(user.id, id=image_id)
        if not image:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Image not found")

    headers = {"Cache-Control": "no-cache"}
    return Response(
        content=image.image_data,
        headers=headers,
        media_type="image/png",
    )


@router.delete("/{image_id}", status_code=204, summary="Delete image by id")
async def v1_delete_image(image_id: int, session_uuid: RequireSessionUUID):
    """Delete image by id"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        image = dbi.get_user_images(user.id, id=image_id)
        if not image:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Image not found")
        if image.owner_id != user.id:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        if image.id == user.image_id:
            dbi.update_user_profile(user.id, image_id=None)
        dbi.delete_image(image_id)

    return {}
