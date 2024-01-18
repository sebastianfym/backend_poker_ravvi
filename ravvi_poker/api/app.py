import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from ..db import DBI

from . import auth
from . import user
from . import images
from . import lobby
from . import clubs
from . import tables
from . import ws
from . import engine


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # statup begin
    logger.info("api startup")
    #await DBI.pool_open()
    await engine.mamager.start()
    await ws.manager.start() #Todo Если все упадет, верни это!
    # statup end
    yield
    # shutdown begin
    await ws.manager.stop()
    await engine.mamager.stop()
    #await DBI.pool_close()
    logger.info("api stopped")
    # shutdown end


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

v1 = APIRouter(prefix="/v1")
v1.include_router(auth.router)
v1.include_router(user.router)
v1.include_router(images.router)
v1.include_router(lobby.router)
v1.include_router(clubs.router)
v1.include_router(tables.router)
v1.include_router(ws.router)


app.include_router(v1)