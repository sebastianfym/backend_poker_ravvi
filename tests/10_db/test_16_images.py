import logging
import pytest
import asyncio
import time

from ravvi_poker.db.dbi import DBI

@pytest.mark.asyncio
async def test_images(user):

    mime_type = 'test'
    image_data = '123456789'

    # create public image
    async with DBI() as db:
        p_image = await db.create_image(None, mime_type, image_data)
    assert p_image
    assert p_image.id
    assert p_image.owner_id is None

    async with DBI() as db:
        row = await db.get_image(p_image.id)
    assert row
    assert row.id == p_image.id
    assert row.owner_id is None
    assert row.mime_type == mime_type
    assert row.image_data == image_data

    # create user image
    async with DBI() as db:
        u_image = await db.create_image(user.id, mime_type, image_data)
    assert u_image
    assert u_image.id
    assert u_image.owner_id == user.id

    async with DBI() as db:
        row = await db.get_image(p_image.id)
    assert row
    assert row.id == p_image.id
    assert row.owner_id is None
    assert row.mime_type == mime_type
    assert row.image_data == image_data

    # list images
    async with DBI() as db:
        rows = await db.get_images_for_user(user.id)
    assert rows
    images = [r for r in rows if r.id in (p_image.id, u_image.id)]
    assert len(images) == 2
    for x in images:
        assert x.owner_id in (None, user.id)
        assert x.mime_type == mime_type

    
