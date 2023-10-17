from io import BytesIO
import base64

from ravvi_poker.db.dbi import DBI
from ravvi_poker.api.images import Image, resize_image, magic

import magic
from PIL import Image


with open("/home/kedikx/Downloads/222-2225760_circle-hd-png-download.png","rb") as f:
    image_data = f.read()
with Image.open(BytesIO(image_data)) as im:
    print(im)

resized = resize_image(image_data)
image_mime_type = magic.from_buffer(resized, mime=True)
print(image_mime_type)
with Image.open(BytesIO(resized)) as im:
    print(im)
image_data = base64.b64encode(resized).decode()
with DBI() as db:
    db.create_user_image(None, image_data, image_mime_type)


