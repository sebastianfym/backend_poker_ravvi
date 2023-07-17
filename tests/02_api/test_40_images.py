import base64
import random

from fastapi.testclient import TestClient
from psycopg.rows import namedtuple_row

from ravvi_poker.api.main import app
from ravvi_poker.db.dbi import DBI

client = TestClient(app)

IMAGES = [
    ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAAECAIAAADAusJtAAAAFklEQVR4nGKa4XaPiYGBAYYBAQAA//8YYgHFJSm6pAAAAABJRU5ErkJggg==", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAAECAIAAADAusJtAAAAFklEQVR4nGI6GiXFxMDAAMOAAAAA//8SKQFCCNiyPAAAAABJRU5ErkJggg==", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAAECAIAAADAusJtAAAAFklEQVR4nGJ65BDBxMDAAMOAAAAA//8VlgGDnSVGagAAAABJRU5ErkJggg==", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAAECAIAAADAusJtAAAAFklEQVR4nGIK3CbAxMDAAMOAAAAA//8P4wEgk7DPdAAAAABJRU5ErkJggg==", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAAECAIAAADAusJtAAAAFklEQVR4nGKK8rrAxMDAAMOAAAAA//8UQgF9P3dN2QAAAABJRU5ErkJggg==", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAF0lEQVR4nGLJsZnFwMDAxAAGgAAAAP//Dz4BSUqmw94AAAAASUVORK5CYII=", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAF0lEQVR4nGKxySxiYGBgYgADQAAAAP//DTIBHsuLPQIAAAAASUVORK5CYII=", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAF0lEQVR4nGJZsvcuAwMDEwMYAAIAAP//GwMCRdYOLrcAAAAASUVORK5CYII=", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAF0lEQVR4nGJZd+o8AwMDEwMYAAIAAP//G4cCTlAWZ+gAAAAASUVORK5CYII=", "image/png"),
    ("iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAF0lEQVR4nGJ5OfkDAwMDEwMYAAIAAP//HV0Cc1XXd14AAAAASUVORK5CYII=", "image/png"),
]


class TestImageManager:
    __test__ = False

    def __init__(self, images=IMAGES) -> None:
        self.images = images
        self.uploaded_images = []

    def __call__(self, *args, **kwargs):
        self.uploaded_images = self.upload_images(*args, **kwargs)
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.delete_images()
        self.uploaded_images = []

    def upload_images(self, user_id=None, images_num=None):
        k = images_num if images_num else len(self.images)
        random_images = random.choices(self.images, k=k)
        with DBI() as dbi:
            with dbi.cursor(row_factory=namedtuple_row) as cursor:
                values = ", ".join(["(%s, %s, %s)"] * len(random_images))
                sql = (
                    f"INSERT INTO image (owner_id, image_data, mime_type)"
                    f" VALUES {values} RETURNING *"
                )
                cursor.execute(
                    sql, sum([[user_id, *image] for image in random_images], [])
                )
                return cursor.fetchall()

    def delete_images(self):
        with DBI() as dbi:
            with dbi.cursor(row_factory=namedtuple_row) as cursor:
                values = ", ".join(["%s"] * len(self.uploaded_images))
                ids = [image.id for image in self.uploaded_images]
                cursor.execute(f"DELETE FROM image WHERE id in ({values})", ids)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200

    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username


def test_delete_image():
    # register user
    access_token, _ = register_guest()

    # upload image
    headers = {"Authorization": "Bearer " + access_token}
    json = {"image_data": IMAGES[0][0]}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200

    image = response.json()
    assert image["id"]
    assert image["is_owner"] is True

    # set image as avatar
    json = {"image_id": image["id"]}
    response = client.patch("/v1/user/profile", json=json, headers=headers)
    assert response.status_code == 200

    # check profile
    profile = response.json()
    assert profile["image_id"] == image["id"]

    # delete image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 204

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()
    assert profile["image_id"] is None

    # check image
    response = client.get(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 404

    # delete non image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 404

    # create image manager
    image_manager = TestImageManager()

    # create common image
    with image_manager(images_num=1) as im:
        uploaded_images = im.uploaded_images
        common_image = uploaded_images[0]
        common_image_id = common_image.id

        # get common image
        response = client.get(f"/v1/images/{common_image_id}", headers=headers)
        assert response.status_code == 200

        # delete common image
        response = client.delete(f"/v1/images/{common_image_id}", headers=headers)
        assert response.status_code == 403

        # get common image
        response = client.get(f"/v1/images/{common_image_id}", headers=headers)
        assert response.status_code == 200

    # register new user
    new_access_token, _ = register_guest()

    # get new user profile
    new_headers = {"Authorization": "Bearer " + new_access_token}
    new_response = client.get("/v1/user/profile", headers=new_headers)
    assert new_response.status_code == 200
    new_profile = new_response.json()

    # TODO переписать на эндпойнт создания изображения
    # create new user image
    with image_manager(user_id=new_profile["id"], images_num=1) as im:
        uploaded_images = im.uploaded_images
        new_user_image = uploaded_images[0]
        new_user_image_id = new_user_image.id

        # get new user image
        response = client.get(f"/v1/images/{new_user_image_id}", headers=new_headers)
        assert response.status_code == 200

        # delete new user image by user
        response = client.delete(f"/v1/images/{new_user_image_id}", headers=headers)
        assert response.status_code == 404

        # get new user image
        response = client.get(f"/v1/images/{new_user_image_id}", headers=new_headers)
        assert response.status_code == 200


def test_upload_image():
    # register user
    access_token, _ = register_guest()

    # upload image
    headers = {"Authorization": "Bearer " + access_token}
    json = {"image_data": IMAGES[0][0]}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200

    # check image
    image = response.json()
    assert image["id"]
    assert image["is_owner"] is True

    # upload same image
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200

    # check same image
    same_image = response.json()
    assert same_image["id"] == image["id"]

    # delete image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 204

    # create image manager
    image_manager = TestImageManager()

    # TODO сейчас это работает только из-за proportion <= 1
    # переделать в соответствии с новой логикой
    # create common image
    with image_manager(images_num=1) as im:
        uploaded_images = im.uploaded_images
        common_image = uploaded_images[0]

        # upload same common image
        json = {"image_data": common_image.image_data}
        response = client.post("/v1/images", json=json, headers=headers)
        assert response.status_code == 200

        # check same common image
        same_common_image = response.json()
        assert same_common_image["id"] == common_image.id
        assert same_common_image["is_owner"] is False


def test_get_available_images():
    # register user
    access_token, _ = register_guest()

    # get available images
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/images", headers=headers)
    assert response.status_code == 200

    # check available images
    available_images = response.json()
    assert not available_images["images"]

    # upload image
    json = {"image_data": IMAGES[0][0]}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200
    image = response.json()

    # get available images
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/images", headers=headers)
    assert response.status_code == 200

    # check available images
    available_images = response.json()
    assert image["id"] in [image["id"] for image in available_images["images"]] 

    # delete image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 204

    # create image manager
    image_manager = TestImageManager()

    # create common image
    with image_manager(images_num=1) as im:
        uploaded_images = im.uploaded_images
        common_image = uploaded_images[0]

        # get available images
        headers = {"Authorization": "Bearer " + access_token}
        response = client.get("/v1/images", headers=headers)
        assert response.status_code == 200

        available_images = response.json()
        assert common_image.id in [image["id"] for image in available_images["images"]]

    # register new user
    new_access_token, _ = register_guest()

    # get new user profile
    new_headers = {"Authorization": "Bearer " + new_access_token}
    new_response = client.get("/v1/user/profile", headers=new_headers)
    assert new_response.status_code == 200
    new_profile = new_response.json()

    # TODO переписать на эндпойнт создания изображения
    # create new user image
    with image_manager(user_id=new_profile["id"], images_num=1) as im:
        uploaded_images = im.uploaded_images
        new_user_image = uploaded_images[0]

        # get new user image
        response = client.get(f"/v1/images/{new_user_image.id}", headers=new_headers)
        assert response.status_code == 200

        # get available images by user
        headers = {"Authorization": "Bearer " + access_token}
        response = client.get("/v1/images", headers=headers)
        assert response.status_code == 200

        available_images = response.json()
        assert new_user_image.id not in [
            image["id"] for image in available_images["images"]
        ]


def test_set_user_avatar():
    # register user
    access_token, _ = register_guest()

    # upload image
    json = {"image_data": IMAGES[0][0]}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/images", json=json, headers=headers)
    assert response.status_code == 200
    image = response.json()

    # set image as avatar
    json = {"image_id": image["id"]}
    response = client.patch("/v1/user/profile", json=json, headers=headers)
    assert response.status_code == 200

    # check profile
    profile = response.json()
    assert profile["image_id"] == image["id"]

    # delete image
    response = client.delete(f"/v1/images/{image['id']}", headers=headers)
    assert response.status_code == 204

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()
    assert profile["image_id"] is None

    # create image manager
    image_manager = TestImageManager()

    # create common image
    with image_manager(images_num=1) as im:
        uploaded_images = im.uploaded_images
        common_image = uploaded_images[0]

        # set common image as profile avatar
        json = {"image_id": common_image.id}
        response = client.patch("/v1/user/profile", json=json, headers=headers)
        assert response.status_code == 200

        # check profile avatar
        profile = response.json()
        assert profile["image_id"] == common_image.id

        # set profile avatar as none
        json = {"image_id": None}
        response = client.patch("/v1/user/profile", json=json, headers=headers)
        assert response.status_code == 200
