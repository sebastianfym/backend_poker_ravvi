
from fastapi import FastAPI, APIRouter
from . import auth
from . import user
from . import clubs
from . import tables
from . import ws
from . import ws_test2

v1 = APIRouter(prefix="/v1")
v1.include_router(auth.router)
v1.include_router(user.router)
v1.include_router(clubs.router)
v1.include_router(tables.router)
v1.include_router(ws.router)
v1.include_router(ws_test2.router)

app = FastAPI()
app.include_router(v1)
