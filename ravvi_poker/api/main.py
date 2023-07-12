
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from . import auth
from . import user
from . import images
from . import clubs
from . import tables
from . import ws
from . import ws_test2

v1 = APIRouter(prefix="/v1")
v1.include_router(auth.router)
v1.include_router(user.router)
v1.include_router(images.router)
v1.include_router(clubs.router)
v1.include_router(tables.router)
v1.include_router(ws.router)
v1.include_router(ws_test2.router)

app = FastAPI()

origins = [
    "http://80.250.80.58",
    "http://localhost",
    "http://127.0.0.1",
    "http://0.0.0.0",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1)
