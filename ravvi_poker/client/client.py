import logging
import asyncio
import aiohttp
import websockets
from ravvi_poker.api.auth import UserAccessProfile
from ravvi_poker.api.user import UserPrivateProfile
from ravvi_poker.engine.events import Message, MessageType, CommandType
from ravvi_poker.engine.poker.bet import Bet

logger = logging.getLogger(__name__)

class PokerClient:
    API_HOST = '127.0.0.1:5001'
    USE_SSL = False

    def __init__(self, *, host=None, use_ssl=None) -> None:
        self.base_url = f"{'https' if use_ssl or self.USE_SSL else 'http'}://{host or self.API_HOST}/"
        self.session = None
        self.ws = None
        self.access_profile = None
        self.table_handlers = {}

    @property
    def user_id(self):
        return self.access_profile.user.id if self.access_profile else None
    
    # CONTEXT

    async def __aenter__(self):
        headers = {"Accept": "application/json"}
        if self.access_profile and self.access_profile.access_token:
            headers["Authorization"] = "Bearer " + self.access_profile.access_token
        self.session = aiohttp.ClientSession(self.base_url, headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if self.ws:
            await self.ws_close()
        if self.session:
            await self.session.close()
            self.session = None

    # WS
    
    async def ws_connect(self):
        params = {}
        if self.access_profile and self.access_profile.access_token:
            params["access_token"] = self.access_profile.access_token
        self.ws = await self.session.ws_connect('/v1/ws', params=params)
        self.ws_task = asyncio.create_task(self.ws_reader())

    async def ws_reader(self):
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                payload = msg.json()
                payload = Message(**payload)
                logger.debug("msg: %s", payload)
                table_id = payload.table_id
                handler = self.table_handlers[table_id]
                if handler:
                    await handler(payload)
            else:
                logger.warn("unknown msg: %s", msg)

    async def ws_close(self):
        await self.ws.close()
        await self.ws_task
        self.ws = None
        self.ws_task = None

    async def ws_send(self, **kwargs):
        logger.info('cmd: %s', kwargs)
        await self.ws.send_json(kwargs)

    # HELPERS
            
    async def _get_result(self, response):
        payload = None
        if response.ok:
            payload = await response.json()
        return response.status, payload

    # AUTH
    
    async def auth_register(self, *, device_token=None, device_props=None):
        body = dict(device_token=device_token, device_props=device_props or {})
        response = await self.session.post('/v1/auth/register', json=body)
        status, payload = await self._get_result(response)
        if status == 200:
            self.access_profile = UserAccessProfile(**payload)
            self.session.headers["Authorization"] = "Bearer " + self.access_profile.access_token

    async def auth_logout(self):
        response = await self.session.post('/v1/auth/logout')
        await self._get_result(response)
        self.access_profile = None
        self.session.headers.popall("Authorization",None)

    # USER
        
    async def get_user_profile(self):
        user_profile = None
        response = await self.session.get('/v1/user/profile')
        status, payload = await self._get_result(response)
        if status == 200:
            user_profile = UserPrivateProfile(**payload)
            self.access_profile.user = user_profile
        return user_profile
    
    # PLAY

    async def join_table(self, table_id, take_seat, table_msg_handler):
        if not self.ws:
            await self.ws_connect()
        self.table_handlers[table_id] = table_msg_handler
        await self.ws_send(cmd_type=CommandType.JOIN, table_id=table_id, take_seat=take_seat)

    async def exit_table(self, table_id):
        if table_id not in self.table_handlers:
            return
        await self.ws_send(cmd_type=CommandType.EXIT)
        del self.table_handlers[table_id]

    # BASIC SIMPLE PLAY STRATEGIES

    async def play_fold_always(self, msg: Message):
        if msg.msg_type == MessageType.GAME_PLAYER_MOVE and msg.user_id == self.user_id:
            logger.info("%s: bet options %s", msg.table_id, msg.options)
            await self.ws_send(cmd_type=CommandType.BET, table_id=msg.table_id, bet=1)

    async def play_check_or_fold(self, msg: Message):
        if msg.msg_type == MessageType.GAME_PLAYER_MOVE and msg.user_id == self.user_id:
            logger.info("%s: bet options %s", msg.table_id, msg.options)
            if Bet.CHECK in msg.options:
                await self.ws_send(cmd_type=CommandType.BET, table_id=msg.table_id, bet=Bet.CHECK)
            else:
                await self.ws_send(cmd_type=CommandType.BET, table_id=msg.table_id, bet=Bet.FOLD)

