import base64
from math import ceil
from io import BytesIO

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import Response
import magic
from PIL import Image
from pydantic import BaseModel, field_validator
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from ..db.dbi import DBI
from .auth import SessionUUID, get_session_and_user

router = APIRouter(prefix="/images", tags=["images"])

ALLOWED_IMAGE_MIME_TYPES = [
    "image/jpeg",
    "image/png"
]

MAX_IMAGE_DIMENSION = 500

class ImageProfile(BaseModel):
    id: int
    is_owner: bool


class ImageProfileList(BaseModel):
    images: list[ImageProfile]


class ImageUpload(BaseModel):
    image_data: str

    @field_validator("image_data")
    def validate_image_data(cls, value):
        try:
            image = base64.b64decode(value, validate=True)
        except Exception:
            raise ValueError("wrong value")
        image_mime_type = magic.from_buffer(image, mime=True)
        if image_mime_type not in ALLOWED_IMAGE_MIME_TYPES:
            raise ValueError("wrong type")
        return value


@router.get("", summary="Get available images")
async def v1_get_available_images(session_uuid: SessionUUID):
    """Get available images"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        images = dbi.get_user_images(user.id)

    return ImageProfileList(images=[
        ImageProfile(
            id=image.id,
            is_owner=(image.owner_id==user.id)
        ) for image in images
    ])


def resize_image(image: bytes) -> bytes:
    with Image.open(BytesIO(image)) as im:
        width, height = im.size
        im_max_dimension = max(width, height)
        proportion = im_max_dimension / MAX_IMAGE_DIMENSION
        if proportion <= 1:
            return image
        resized_im = im.resize((ceil(width/proportion), ceil(height/proportion)))
        buf = BytesIO()
        resized_im.save(buf, format=im.format)
        return buf.getvalue()

@router.post("", summary="Upload image")
async def v1_upload_image(params: ImageUpload, session_uuid: SessionUUID):
    """Upload image"""

    image = base64.b64decode(params.image_data, validate=True)
    image_mime_type = magic.from_buffer(image, mime=True)
    image = resize_image(image)
    image_data = base64.b64encode(image).decode()

    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        image = dbi.get_user_images(user.id, image_data=image_data)
        if not image:
            image = dbi.create_user_image(user.id, image_data, image_mime_type)

    return ImageProfile(
        id=image.id,
        is_owner=(image.owner_id==user.id)
    )


@router.get("/{image_id}", summary="Get image by id")
async def v1_get_image(image_id: int, session_uuid: SessionUUID):
    """Get image by id"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        image = dbi.get_image(image_id=image_id)
        if not image:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Image not found")

    headers = {"Cache-Control": "no-cache"}
    return Response(
        content=base64.b64decode(image.image_data),
        headers=headers,
        media_type=image.mime_type,
    )


@router.delete("/{image_id}", status_code=204, summary="Delete image by id")
async def v1_delete_image(image_id: int, session_uuid: SessionUUID):
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
        user_clubs = dbi.get_clubs_for_user(user_id=user.id)
        [dbi.update_club(club.id, image_id=None) for club in user_clubs if club.image_id == image_id]
        dbi.delete_image(image_id)

    return {}
