from fastapi import FastAPI, APIRouter
from . import auth
from . import user
from . import ws_test

v1 = APIRouter(prefix="/v1")
v1.include_router(auth.router)
v1.include_router(user.router)
v1.include_router(ws_test.router)

app = FastAPI()
app.include_router(v1)
