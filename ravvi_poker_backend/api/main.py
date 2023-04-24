from fastapi import FastAPI, APIRouter
from . import auth
from . import user

v1 = APIRouter(prefix='/v1')
v1.include_router(auth.router)
v1.include_router(user.router)

app = FastAPI()
app.include_router(v1)