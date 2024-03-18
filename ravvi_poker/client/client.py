import logging
import asyncio

import aiohttp
import websockets
from fastapi import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from ravvi_poker.api.auth import UserAccessProfile
from ravvi_poker.api.clubs import ClubProfile, ClubMemberProfile
from ravvi_poker.api.images import ImageProfile
from ravvi_poker.api.tables import TableProfile
from ravvi_poker.api.types import UserPublicProfile
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

    async def update_user_profile(self, name=None, image_id=None):
        data = {
            "name": name,
            "image_id": image_id
        }
        response = await self.session.patch('/v1/user/profile', json=data)
        status, payload = await self._get_result(response)
        if status == 200:
            user_profile = UserPrivateProfile(**payload)
            self.access_profile.user = user_profile
            return user_profile
        else:
            raise "Check the correctness of the data"

    async def get_user_by_id(self, id=None):
        response = await self.session.get(f'/v1/user/{id}')
        status, payload = await self._get_result(response)
        if status == 200:
            user_profile = UserPublicProfile(**payload)
            return user_profile
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User with this id not found")

    # IMAGES

    async def get_available_images(self):
        response = await self.session.get('/v1/images')
        status, payload = await self._get_result(response)
        if status == 200:
            img_list = []
            for img in payload:
                img_list.append(ImageProfile(**img))
            return img_list
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    # CLUBS

    async def create_club(self, name=None, description=None, image_id=None, user_role="O", user_approved=False, timezone=None):
        data = {
            "name": name,
            "description": description,
            "image_id": image_id,
            "user_role": user_role,
            "user_approved": user_approved,
            "timezone": timezone
        }
        response = await self.session.post('/v1/clubs', json=data)
        status, payload = await self._get_result(response)
        if status == 201:
            return ClubProfile(**payload)
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def get_club_by_id(self, club_id=None):
        response = await self.session.get(f'/v1/clubs/{club_id}')
        status, payload = await self._get_result(response)
        if status == 200:
            return ClubProfile(**payload)
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def update_club(self, club_id, name=None, description=None, image_id=None, timezone=None, automatic_confirmation=False):
        data = {
            "name": name,
            "description": description,
            "image_id": image_id,
            "timezone": timezone,
            "automatic_confirmation": automatic_confirmation
        }
        response = await self.session.patch(f'/v1/clubs/{club_id}', json=data)
        status, payload = await self._get_result(response)
        if status == 200:
            return ClubProfile(**payload)
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def get_all_clubs(self):
        response = await self.session.get('/v1/clubs')
        status, payload = await self._get_result(response)
        if status == 200:
            club_list = []
            for club in payload:
                club_list.append(ClubProfile(**club))
            return club_list
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def get_clubs_members(self, club_id=None):
        response = await self.session.get(f'/v1/clubs/{club_id}/members')
        status, payload = await self._get_result(response)
        if status == 200:
            members_list = []
            for member in payload:
                members_list.append(ClubMemberProfile(**member))
            return members_list
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def send_req_join_in_club(self, club_id=None, user_comment=None):
        response = await self.session.post(f'/v1/clubs/{club_id}/members', json={"user_comment":user_comment})
        status, payload = await self._get_result(response)
        if status == 200:
            return ClubProfile(**payload)
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def get_request_to_join(self, club_id):
        response = await self.session.get(f'/v1/clubs/{club_id}/members/requests')
        status, payload = await self._get_result(response)
        if status == 200:
            requests_list = []
            for member_req in payload:
                requests_list.append(ClubMemberProfile(**member_req))
            return requests_list
        elif status == 403:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def approve_req_to_join(self, club_id, user_id, rakeback=None, agent_id=None, nickname=None, comment=None, user_role=None):
        data = {
            "rakeback": rakeback,
            "agent_id": agent_id,
            "nickname": nickname,
            "comment": comment,
            "user_role": user_role
        }
        response = await self.session.put(f'/v1/clubs/{club_id}/members/{user_id}', json=data)
        status, payload = await self._get_result(response)
        if status == 200:
            return ClubMemberProfile(**payload)
        elif status == 403:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def reject_req_to_join(self, club_id, user_id):
        response = await self.session.delete(f'/v1/clubs/{club_id}/members/{user_id}', json={})
        status, payload = await self._get_result(response)
        if status == 200:
            return status
        elif status == 403:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    # TABLE

    async def create_table(self, club_id=None, table_type=None, table_name=None, table_seats=None, game_type=None,
                           game_subtype=None, buyin_cost=None):

        data = {
            "table_type": table_type,
            "table_name": table_name,
            "table_seats": table_seats,
            "game_type": game_type,
            "game_subtype": game_subtype,
            "buyin_cost": buyin_cost,
        }

        response = await self.session.post(f'/v1/clubs/{club_id}/tables', json=data)
        status, payload = await self._get_result(response)
        if status == 201:
            return TableProfile(**payload)
        elif status == 403:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def get_club_tables(self, club_id):
        response = await self.session.get(f'/v1/clubs/{club_id}/tables')
        status, payload = await self._get_result(response)
        if status == 200:
            return TableProfile(**payload)
        elif status == 403:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif status == 404:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

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

