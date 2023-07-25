import base64
from io import BytesIO
from math import ceil
import random

from fastapi.testclient import TestClient
import magic
from PIL import Image

from ravvi_poker.api.images import MAX_IMAGE_DIMENSION
from ravvi_poker.api.main import app
from ravvi_poker.db.dbi import DBI

client = TestClient(app)

WEBP_BASE64_IMAGE = (
    "UklGRlgAAABXRUJQVlA4IEwAAABwBgCdASqAAIAAPpFIoUylpCMiIIgAsBIJaW7hdJAAT22Iv"
    "EFRz2xF4gqOe2IvEFRz2xF4gqOe2IvEE2AA/v6USL/xd2I4ySAAAAAA"
)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200

    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username


class TestImage():
    __test__ = False

    def __init__(self, mode="RGB", size=(128, 128), color=None, format="png", user_id=None):
        self.mode = mode
        self.size = size
        self.color = color if color else tuple([random.randint(0, 255) for _ in range(3)])
        self.format = format
        self.user_id = user_id
        self._db_image = None

    def __enter__(self):
        self._db_image = self.upload_image()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.delete_image()
        self._db_image = None

    def upload_image(self):
        with DBI() as dbi:
            return dbi.create_user_image(self.user_id, self.base64, self.mime_type)

    def delete_image(self):
        with DBI() as dbi:
            dbi.delete_image(self._db_image.id)

    @property
    def bytes(self):
        im = Image.new(self.mode, self.size, self.color)
        buf = BytesIO()
        im.save(buf, format=self.format)
        return buf.getvalue()

    @property
    def base64(self):
        return base64.b64encode(self.bytes).decode()

    @property
    def db(self):
        return self._db_image

    @property
    def mime_type(self):
        return magic.from_buffer(self.bytes, mime=True)


def test_set_user_avatar():
    # register user
    access_token, _ = register_guest()

    # get user profile
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()

    # with user image
    with TestImage(user_id=profile["id"]) as im:
        # set image as profile avatar
        json = {"image_id": im.db.id}
        response = client.patch("/v1/user/profile", json=json, headers=headers)
        assert response.status_code == 200

        # check profile
        profile = response.json()
        assert profile["image_id"] == im.db.id

        # unset profile avatar
        json = {"image_id": None}
        response = client.patch("/v1/user/profile", json=json, headers=headers)
        assert response.status_code == 200

    # with common image
    with TestImage() as im:
        # set common image as profile avatar
        json = {"image_id": im.db.id}
        response = client.patch("/v1/user/profile", json=json, headers=headers)
        assert response.status_code == 200

        # check profile avatar
        profile = response.json()
        assert profile["image_id"] == im.db.id

        # unset profile avatar
        json = {"image_id": None}
        response = client.patch("/v1/user/profile", json=json, headers=headers)
        assert response.status_code == 200


def test_set_club_avatar():
    # register user
    access_token, _ = register_guest()

    # get user profile
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()

    # create club
    response = client.post("/v1/clubs", json={}, headers=headers)
    assert response.status_code == 201

    club = response.json()

    # with user image
    with TestImage(user_id=profile["id"]) as im:
        # set image as club avatar
        json = {"image_id": im.db.id}
        response = client.patch(f"/v1/clubs/{club['id']}", json=json, headers=headers)
        assert response.status_code == 200

        # check club
        club = response.json()
        assert club["image_id"] == im.db.id

        # unset club avatar
        json = {"image_id": None}
        response = client.patch(f"/v1/clubs/{club['id']}", json=json, headers=headers)
        assert response.status_code == 200

    # with common image
    with TestImage() as im:
        # set common image as club avatar
        json = {"image_id": im.db.id}
        response = client.patch(f"/v1/clubs/{club['id']}", json=json, headers=headers)
        assert response.status_code == 200

        # check club
        club = response.json()
        assert club["image_id"] == im.db.id

        # unset club avatar
        json = {"image_id": None}
        response = client.patch(f"/v1/clubs/{club['id']}", json=json, headers=headers)
        assert response.status_code == 200


def test_delete_image():
    # register user
    access_token, _ = register_guest()

    # upload image
    headers = {"Authorization": "Bearer " + access_token}
    im = TestImage()
    json = {"image_data": im.base64}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200

    # check image
    image = response.json()
    assert image["id"]
    assert image["is_owner"] is True

    # delete image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 204

    # check non-existent image
    response = client.get(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 404

    # try to delete non-existent image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 404

    # with common image
    with TestImage() as im:
        # get common image
        response = client.get(f"/v1/images/{im.db.id}", headers=headers)
        assert response.status_code == 200

        # try to delete common image
        response = client.delete(f"/v1/images/{im.db.id}", headers=headers)
        assert response.status_code == 403

    # register new user
    new_access_token, _ = register_guest()

    # get new user profile
    new_headers = {"Authorization": "Bearer " + new_access_token}
    new_response = client.get("/v1/user/profile", headers=new_headers)
    assert new_response.status_code == 200

    new_profile = new_response.json()

    # with new user image
    with TestImage(user_id=new_profile["id"]) as im:
        # get new image by new user
        response = client.get(f"/v1/images/{im.db.id}", headers=new_headers)
        assert response.status_code == 200

        # try to delete new image by user
        response = client.delete(f"/v1/images/{im.db.id}", headers=headers)
        assert response.status_code == 404


def test_delete_in_use_image():
    # register user
    access_token, _ = register_guest()

    # get user profile
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()

    # with user images
    with TestImage(user_id=profile["id"]) as im1, TestImage(user_id=profile["id"]) as im2:
        # set im1 as avatar
        json = {"image_id": im1.db.id}
        response = client.patch("/v1/user/profile", json=json, headers=headers)
        assert response.status_code == 200

        # check profile
        profile = response.json()
        assert profile["image_id"] == im1.db.id

        # create club1 with im1 avatar
        response = client.post("/v1/clubs", json=json, headers=headers)
        assert response.status_code == 201

        # check club1
        club1 = response.json()
        assert club1["image_id"] == im1.db.id

        # create club2 with im1 avatar
        response = client.post("/v1/clubs", json=json, headers=headers)
        assert response.status_code == 201

        club2 = response.json()
        assert club2["image_id"] == im1.db.id

        # create club3 with im2 avatar
        json = {"image_id": im2.db.id}
        response = client.post("/v1/clubs", json=json, headers=headers)
        assert response.status_code == 201

        club3 = response.json()
        assert club3["image_id"] == im2.db.id

        # delete im1
        response = client.delete(f"/v1/images/{im1.db.id}", headers=headers)
        assert response.status_code == 204

        # check profile
        response = client.get("/v1/user/profile", headers=headers)
        assert response.status_code == 200

        profile = response.json()
        assert profile["image_id"] is None

        # get clubs
        response = client.get("/v1/clubs", headers=headers)
        assert response.status_code == 200

        clubs = response.json()
        clubs.sort(key=lambda x: x["id"])

        assert clubs[0]["image_id"] is None
        assert clubs[1]["image_id"] is None
        assert clubs[2]["image_id"] == club3["image_id"]

        # unset club3 avatar
        json = {"image_id": None}
        response = client.patch(f"/v1/clubs/{club3['id']}", json=json, headers=headers)
        assert response.status_code == 200


def test_upload_image():
    # register user
    access_token, _ = register_guest()

    # upload invalid image
    headers = {"Authorization": "Bearer " + access_token}
    im = "invalid image data"
    json = {"image_data": im}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 422

    # upload image with prohibited mime type
    json = {"image_data": WEBP_BASE64_IMAGE}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 422

    # upload image without resizing
    im_dim = ceil(MAX_IMAGE_DIMENSION / 4)
    im = TestImage(size=(im_dim, im_dim))
    json = {"image_data": im.base64}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200

    # check response
    image = response.json()
    assert image["id"]
    assert image["is_owner"] is True

    # get image
    response = client.get(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 200

    # check image
    assert response.headers["Content-Type"] == im.mime_type
    assert base64.b64encode(response.read()).decode() == im.base64

    # delete image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 204

    # upload image with resizing
    im_dim = ceil(MAX_IMAGE_DIMENSION * 1.5)
    im = TestImage(size=(im_dim, im_dim))
    json = {"image_data": im.base64}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200

    # check response
    image = response.json()
    assert image["id"]
    assert image["is_owner"] is True

    # get image
    response = client.get(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 200

    bytes_image = response.read()
    img = Image.open(BytesIO(bytes_image))

    # check image
    assert response.headers["Content-Type"] == im.mime_type
    assert img.size == (MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION)

    # try to upload same image
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200

    same_image = response.json()
    assert same_image["id"] == image["id"]

    # try to upload same resized image
    json = json = {"image_data": base64.b64encode(bytes_image).decode()}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200

    same_image = response.json()
    assert same_image["id"] == image["id"]

    # delete resized image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 204

    # with common image
    with TestImage() as im:
        # try to upload same common image
        json = {"image_data": im.base64}
        response = client.post("/v1/images", json=json, headers=headers)
        assert response.status_code == 200

        same_image = response.json()
        assert same_image["id"] == im.db.id


def test_get_available_images():
    # register user
    access_token, _ = register_guest()

    # get user profile
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()

    # get available images
    response = client.get("/v1/images", headers=headers)
    assert response.status_code == 200

    # check images
    images = response.json()
    assert not images["images"]

    # with user image
    with TestImage(user_id=profile["id"]) as im:
        # get available images
        response = client.get("/v1/images", headers=headers)
        assert response.status_code == 200

        # check images
        images = response.json()
        assert im.db.id in [image["id"] for image in images["images"]]

    # with common image
    with TestImage() as im:
        # get available images
        response = client.get("/v1/images", headers=headers)
        assert response.status_code == 200

        # check images
        images = response.json()
        assert im.db.id in [image["id"] for image in images["images"]]

    # register new user
    new_access_token, _ = register_guest()

    # get new user profile
    new_headers = {"Authorization": "Bearer " + new_access_token}
    new_response = client.get("/v1/user/profile", headers=new_headers)
    assert new_response.status_code == 200

    new_profile = new_response.json()

    # with new user image
    with TestImage(user_id=new_profile["id"]) as im:
        # get available images by user
        response = client.get("/v1/images", headers=headers)
        assert response.status_code == 200

        # check images
        images = response.json()
        assert im.db.id not in [image["id"] for image in images["images"]]
