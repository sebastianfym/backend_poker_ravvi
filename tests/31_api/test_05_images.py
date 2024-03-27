import logging
import pytest
from PIL import Image
from io import BytesIO


from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from fastapi.testclient import TestClient
from ravvi_poker.api.auth_.types import UserAccessProfile
from ravvi_poker.api.images import ImageProfile

log = logging.getLogger(__name__)

def create_dummy_image_data(format, width, height):
    im = Image.new("RGB", (width, height), 127)
    buf = BytesIO()
    im.save(buf, format=format)
    return buf.getvalue()

def test_upload_image(api_client: TestClient, api_guest: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # no image data
    response = api_client.post("/v1/images")
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    image_png =  create_dummy_image_data('PNG', 1024, 800)
    image_jpeg =  create_dummy_image_data('JPEG', 300, 200)

    # sample image data
    response = api_client.post("/v1/images", files={'file': BytesIO(image_png)})
    assert response.status_code == HTTP_200_OK
    image_1 = ImageProfile(**response.json())
    assert image_1.id
    assert image_1.is_owner

    response = api_client.post("/v1/images", files={'file': BytesIO(image_jpeg)})
    assert response.status_code == HTTP_200_OK
    image_2 = ImageProfile(**response.json())
    assert image_2.id
    assert image_2.is_owner

    # get image
    response = api_client.get(f"/v1/images/123456")
    assert response.status_code == HTTP_404_NOT_FOUND

    # get image
    response = api_client.get(f"/v1/images/{image_1.id}")
    assert response.status_code == HTTP_200_OK
    #log.info("%s %s", response, response.headers)
    assert response.headers.get('cache-control')
    assert response.headers.get('content-type') == 'image/png'
    with Image.open(BytesIO(response.content)) as im:
        #log.info("%s %s", im.format, im.size)
        assert im.format == 'PNG'
        assert im.size == (500, 391)

    response = api_client.get(f"/v1/images/{image_2.id}")
    assert response.status_code == HTTP_200_OK
    #log.info("%s %s", response, response.headers)
    assert response.headers.get('cache-control')
    assert response.headers.get('content-type') == 'image/jpeg'
    with Image.open(BytesIO(response.content)) as im:
        #log.info("%s %s", im.format, im.size)
        assert im.format == 'JPEG'
        assert im.size == (300, 200)

    # get image list
    response = api_client.get(f"/v1/images")
    assert response.status_code == HTTP_200_OK
    images = [ImageProfile(**r) for r in response.json()]
    assert images
    own_images = {image.id for image in images if image.is_owner}
    assert image_1.id in own_images
    assert image_2.id in own_images
    #for image in images:
    #    log.info("%s %s", image.id, image.is_owner)

