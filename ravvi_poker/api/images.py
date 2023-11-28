import logging

import base64
from math import ceil
from io import BytesIO

from fastapi import APIRouter, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import Response
import magic
from PIL import Image
from pydantic import BaseModel, field_validator
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from ..db.adbi import DBI as ADBI
from .utils import SessionUUID, get_session_and_user

log = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["images"])

ALLOWED_IMAGE_MIME_TYPES = [
    "image/jpeg",
    "image/png"
]

MAX_IMAGE_DIMENSION = 500

class ImageProfile(BaseModel):
    id: int
    is_owner: bool


@router.post("", summary="Upload image")
async def v1_upload_image(file: UploadFile, session_uuid: SessionUUID):
    """Upload image"""
    async with ADBI() as db:
        _, user = await get_session_and_user(db, session_uuid)

        log.info("file %s %s", file.content_type, file.size)
        image_data = await file.read()
        with Image.open(BytesIO(image_data)) as im:
            format = im.format
            width, height = im.size
            max_dim = max(width, height)
            resize_ratio = MAX_IMAGE_DIMENSION/max_dim
            log.info("image %s %s %s", format, width, height)
            if resize_ratio<1:
                im = im.resize((ceil(width*resize_ratio), ceil(height*resize_ratio)))
                width, height = im.size
                log.info("-> image %s %s %s", format, width, height)
            buffer = BytesIO()
            format = 'PNG' if format.upper()=='PNG' else 'JPEG'
            im.save(buffer, format=format)
            image_data = buffer.getvalue()

        mime_type = magic.from_buffer(image_data, mime=True)
        log.info("image %s %s", mime_type, len(image_data))

        image = await db.create_image(user.id, mime_type, image_data)

    return ImageProfile(
        id=image.id,
        is_owner=True
    )


@router.get("/{image_id}", summary="Get image by id")
async def v1_get_image(image_id: int, session_uuid: SessionUUID):
    """Get image by id"""
    async with ADBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        image = await db.get_image(image_id)
        if not image:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Image not found")

    headers = {"Cache-Control": "max-age=604800"}
    return Response(
        content=base64.b64decode(image.image_data),
        headers=headers,
        media_type=image.mime_type,
    )

@router.get("", summary="Get available images")
async def v1_get_avaiable_image(session_uuid: SessionUUID):
    """Get images for user"""
    async with ADBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        images = await db.get_images_for_user(user.id)

    return [ImageProfile(id=image.id, is_owner=image.owner_id==user.id) for image in images]
