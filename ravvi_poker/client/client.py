import datetime
import logging
import asyncio


import aiohttp
from random import SystemRandom
from time import perf_counter
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from ravvi_poker.api.auth.types import UserAccessProfile
from ravvi_poker.api.clubs.types import ClubProfile, ClubMemberProfile, MemberAccountDetailInfo, AccountDetailInfo, \
    ClubBalance, ChipsTxnItem, TableProfile
from ravvi_poker.api.images import ImageProfile
# from ravvi_poker.api.tables import TableProfile
# from ravvi_poker.api.types import UserPublicProfile
from ravvi_poker.api.users.types import UserPrivateProfile, UserPublicProfile
from ravvi_poker.engine.events import Message, MessageType, CommandType
from ravvi_poker.engine.poker.bet import Bet

logger = logging.getLogger(__name__)

def perf_log(func):
    async def wrapper(self, url, **kwargs):
        t0 = perf_counter()
        response =  await func(self, url, **kwargs)
        t1 = perf_counter()
        logger.info("%s %s %s %s %s", self.user_id, func.__name__, url, response.status, f"{t1-t0:.3f}")
        return response
    return wrapper

class PokerClient:
    API_HOST = '127.0.0.1:5001'
    USE_SSL = False

    def __init__(self, *, host=None, use_ssl=None) -> None:
        self.base_url = f"{'https' if use_ssl or self.USE_SSL else 'http'}://{host or self.API_HOST}"
        self.session = None
        self.ws = None
        self.access_profile = None
        self.table_handlers = {}
        self.device_token = None
        self.rng = SystemRandom()

    @property
    def user_id(self):
        return self.access_profile.user.id if self.access_profile else None

    # CONTEXT

    async def __aenter__(self):
        headers = {"Accept": "application/json"}
        if self.access_profile and self.access_profile.access_token:
            headers["Authorization"] = "Bearer " + self.access_profile.access_token
        connector = aiohttp.TCPConnector(force_close=True, limit=1000)
        self.session = aiohttp.ClientSession(self.base_url, headers=headers, connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if self.ws:
            await self.ws_close()
        if self.session:
            await self.session.close()
            self.session = None

    # HTTP
    @perf_log
    async def GET(self, url, **kwargs):
        return await self.session.get(url, **kwargs)

    @perf_log
    async def POST(self, url, **kwargs):
        return await self.session.post(url, **kwargs)

    @perf_log
    async def PUT(self, url, **kwargs):
        return await self.session.put(url, **kwargs)

    @perf_log
    async def PATCH(self, url, **kwargs):
        return await self.session.patch(url, **kwargs)

    # WS

    async def ws_connect(self):
        params = {}
        if self.access_profile and self.access_profile.access_token:
            params["access_token"] = self.access_profile.access_token
        self.ws = await self.session.ws_connect('/api/v1/ws', params=params)
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
        if response.headers.get('content-type') == 'application/json':
            payload = await response.json()
        return response.status, payload

    async def sleep_random(self, minSeconds, maxSeconds):
        seconds = self.rng.randint(minSeconds, maxSeconds)
        await asyncio.sleep(seconds)

    # AUTH

    async def auth_register(self, *, device_token=None, device_props=None):
        body = dict(device_token=device_token, device_props=device_props or {})
        response = await self.POST('/api/v1/auth/register', json=body)
        status, payload = await self._get_result(response)
        if status == 200:
            self.access_profile = UserAccessProfile(**payload)
            self.session.headers["Authorization"] = "Bearer " + self.access_profile.access_token
        return status, payload

    async def auth_logout(self):
        response = await self.POST('/api/v1/auth/logout')
        status, payload = await self._get_result(response)
        self.access_profile = None
        self.session.headers.popall("Authorization", None)
        return status, payload

    # USER

    async def get_user_profile(self):
        user_profile = None
        response = await self.GET('/api/v1/user/profile')
        status, payload = await self._get_result(response)
        if status == 200:
            #logger.info(f"Get user profile: {datetime.datetime.now()}")
            user_profile = UserPrivateProfile(**payload)
            self.access_profile.user = user_profile
        return status, user_profile

    async def update_user_profile(self, name=None, image_id=None):
        data = {
            "name": name,
            "image_id": image_id
        }
        response = await self.PATCH('/api/v1/user/profile', json=data)
        status, payload = await self._get_result(response)
        if status == 200:
            #logger.info(f"User update account: {datetime.datetime.now()}")
            user_profile = UserPrivateProfile(**payload)
            self.access_profile.user = user_profile
            return status, user_profile
        else:
            # raise "Check the correctness of the data"
            return status, payload

    async def get_user_by_id(self, id=None):
        response = await self.GET(f'/api/v1/user/{id}')
        status, payload = await self._get_result(response)
        if status == 200:
            payload = UserPublicProfile(**payload)
        return status, payload

    async def login_with_username_and_password(self, username, password):
        data = {
            "username": username,
            "password": password
        }
        response = await self.POST(f'/api/v1/auth/login', json=data)
        status, payload = await self._get_result(response)
        if status == 200:
            payload = UserAccessProfile(**payload)
            self.access_profile = payload
            self.session.headers["Authorization"] = "Bearer " + self.access_profile.access_token
        return status, payload

    async def password_update(self, current_password, new_password):
        data = {
            "current_password": current_password,
            "new_password": new_password
        }
        response = await self.POST(f'/api/v1/auth/password', json=data)
        status, payload = await self._get_result(response)
        return status, payload

    # IMAGES

    async def get_available_images(self):
        response = await self.GET('/api/v1/images')
        status, payload = await self._get_result(response)
        if status == 200:
            img_list = []
            for img in payload:
                img_list.append(ImageProfile(**img))
            payload = img_list
        return status, payload

    # LOBBY

    async def get_lobby_entry_tables(self):
        response = await self.GET('/api/v1/lobby/entry_tables')
        status, payload = await self._get_result(response)
        return status, payload

    # CLUBS

    async def create_club(self, name=None, description=None, image_id=None, user_role="O", user_approved=False,
                          timezone=None):
        data = {
            "name": name,
            "description": description,
            "image_id": image_id,
            "user_role": user_role,
            "user_approved": user_approved,
            "timezone": timezone
        }
        response = await self.POST('/api/v1/clubs', json=data)
        status, payload = await self._get_result(response)
        if status == 201:
            #logger.info(f"Owner create club: {datetime.datetime.now()}")
            return status, ClubProfile(**payload)
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def get_club_by_id(self, club_id=None):
        response = await self.GET(f'/api/v1/clubs/{club_id}')
        status, payload = await self._get_result(response)
        if status == 200:
            #logger.info(f"Get club by id: {datetime.datetime.now()}")
            return status, ClubProfile(**payload)
        elif status == 404:
            return status, payload
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            return status, payload
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def update_club(self, club_id, name=None, description=None, image_id=None, timezone=None,
                          automatic_confirmation=False):
        data = {
            "name": name,
            "description": description,
            "image_id": image_id,
            "timezone": timezone,
            "automatic_confirmation": automatic_confirmation
        }
        response = await self.PATCH(f'/api/v1/clubs/{club_id}', json=data)
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"Owner update club: {datetime.datetime.now()}")
            return status, ClubProfile(**payload)
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def get_all_clubs(self):
        response = await self.GET('/api/v1/clubs')
        status, payload = await self._get_result(response)
        if status == 200:
            club_list = []
            for club in payload:
                club_list.append(ClubProfile(**club))
            logger.info(f"Get club list: {datetime.datetime.now()}")
            return status, club_list
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def get_clubs_members(self, club_id=None):
        response = await self.GET(f'/api/v1/clubs/{club_id}/members')
        status, payload = await self._get_result(response)
        if status == 200:
            members_list = []
            for member in payload:
                members_list.append(ClubMemberProfile(**member))
            logger.info(f"Owner get list with members: {datetime.datetime.now()}")
            return status, members_list
        elif status == 404:
            return status, payload
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            return status, payload
#             raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def send_req_join_in_club(self, club_id=None, user_comment=None):
        response = await self.POST(f'/api/v1/clubs/{club_id}/members', json={"user_comment": user_comment})
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"User send req for update balance: {datetime.datetime.now()}")
            return status, ClubProfile(**payload)
        elif status == 404:
            return status, payload
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
        else:
            return status, payload
#             raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")

    async def get_request_to_join(self, club_id):
        response = await self.GET(f'/api/v1/clubs/{club_id}/members/requests')
        status, payload = await self._get_result(response)
        if status == 200:
            requests_list = []
            for member_req in payload:
                requests_list.append(ClubMemberProfile(**member_req))
            logger.info(f"Owner get list with all chips requests: {datetime.datetime.now()}")
            return status, requests_list
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def approve_req_to_join(self, club_id, user_id, rakeback=None, agent_id=None, nickname=None, comment=None,
                                  user_role=None):
        data = {
            "rakeback": rakeback,
            "agent_id": agent_id,
            "nickname": nickname,
            "comment": comment,
            "user_role": user_role
        }
        response = await self.PUT(f'/api/v1/clubs/{club_id}/members/{user_id}', json=data)
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"Accept new member in club: {datetime.datetime.now()}")
            return status, ClubMemberProfile(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def reject_req_to_join(self, club_id, user_id):
        response = await self.session.delete(f'/api/v1/clubs/{club_id}/members/{user_id}', json={})
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"Reject member request to join: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def leave_from_club(self, club_id):
        response = await self.POST(f"/api/v1/clubs/{club_id}/leave_from_club", json={})
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"Member leave from club: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def get_member_info_for_owner(self, club_id, user_id):
        response = await self.POST(f"/api/v1/clubs/{club_id}/profile/{user_id}", json={})
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"Owner get info about member: {datetime.datetime.now()}")
            return status, MemberAccountDetailInfo(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club or user with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def get_detail_member_info(self, club_id):
        response = await self.POST(f"/api/v1/clubs/{club_id}/user_account", json={})
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"Get info about member: {datetime.datetime.now()}")
            return status, AccountDetailInfo(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club or user with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

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

        response = await self.POST(f'/api/v1/clubs/{club_id}/tables', json=data)
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Create new table: {datetime.datetime.now()}")
            return status, TableProfile(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def get_club_tables(self, club_id):
        response = await self.GET(f'/api/v1/clubs/{club_id}/tables')
        status, payload = await self._get_result(response)
        if status == 200:
            result_list = []
            for table in payload:
                result_list.append(TableProfile(**table))
            logger.info(f"Get all tables: {datetime.datetime.now()}")
            return status, result_list
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    # TXN CHIPS
    async def get_club_balance(self, club_id):
        response = await self.GET(f"/api/v1/clubs/{club_id}/club_balance")
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"Owner get club balance: {datetime.datetime.now()}")
            return status, ClubBalance(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def get_club_chips_requests(self, club_id):
        response = await self.GET(f"/api/v1/clubs/{club_id}/requests_chip_replenishment")
        status, payload = await self._get_result(response)
        if status == 200:
            # logger.info(f"Owner get requests on chips: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def get_club_txn_history(self, club_id):
        response = await self.GET(f"/api/v1/info/{club_id}/history")
        status, payload = await self._get_result(response)
        if status == 200:
            logger.info(f"Owner get txns info: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def up_club_balance(self, club_id, amount):
        response = await self.POST(f"/api/v1/chips/{club_id}/club/chips", json={"amount": amount})
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Owner update club balance: {datetime.datetime.now()}")
            return status, ChipsTxnItem(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def down_club_balance(self, club_id, amount):
        response = await self.session.delete(f"/api/v1/chips/{club_id}/club/chips", json={"amount": amount})
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Owner debited balance: {datetime.datetime.now()}")
            return status, ChipsTxnItem(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def up_agent_balance(self, club_id, user_id, amount):
        response = await self.POST(f"/api/v1/chips/{club_id}/agents/chips/{user_id}",
                                           json={"amount": amount, "mode": "give_out"})
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Owner update agent balance: {datetime.datetime.now()}")
            return status, ChipsTxnItem(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def down_agent_balance(self, club_id, user_id, amount):
        response = await self.POST(f"/api/v1/chips/{club_id}/agents/chips/{user_id}",
                                           json={"amount": amount, "mode": "pick_up"})
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Owner debited agent balance: {datetime.datetime.now()}")
            return status, ChipsTxnItem(**payload)
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def up_user_balance(self, club_id, amount, user_list):
        data = {
            "amount": amount,
            "club_member": user_list
        }
        response = await self.POST(f"/api/v1/chips/{club_id}/players/chips", json=data)
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Owner update user balance: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def down_user_balance(self, club_id, amount, user_list):
        data = {
            "mode": "pick_up",
            "amount": amount,
            "club_member": user_list
        }
        response = await self.POST(f"/api/v1/chips/{club_id}/players/chips", json=data)
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Owner debited user balance: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def send_req_to_up_user_balance(self, club_id, amount):
        response = await self.POST(f"/api/v1/chips/{club_id}/requests/chips",
                                           json={"amount": amount, "agent": False})
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"member send request to update balance: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def send_req_to_up_agent_balance(self, club_id, amount):
        response = await self.POST(f"/api/v1/chips/{club_id}/requests/chips",
                                           json={"amount": amount, "agent": True})
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"member send request to update agent balance: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def accept_all_balance_requests(self, club_id):
        response = await self.POST(f"/api/v1/chips/{club_id}/requests/chips/all",
                                           json={"operation": "approve"})
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Owner accept all chips requests: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def reject_all_balance_requests(self, club_id):
        response = await self.POST(f"/api/v1/chips/{club_id}/requests/chips/all",
                                           json={"operation": "reject"})
        status, payload = await self._get_result(response)
        if status == 201:
            logger.info(f"Owner reject all chips requests: {datetime.datetime.now()}")
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club with this id not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    # INFO

    async def levels_schedule(self, table_type):
        response = await self.GET(f"/api/v1/info/levels_schedule/{table_type}")
        status, payload = await self._get_result(response)
        if status == 200:
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Page not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def rewards_distribution(self):
        response = await self.GET(f"/api/v1/info/rewards_distribution")
        status, payload = await self._get_result(response)
        if status == 200:
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Page not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

    async def countries(self, language):
        response = await self.GET(f"/api/v1/info/countries/{language}")
        status, payload = await self._get_result(response)
        if status == 200:
            return status, payload
        elif status == 403:
            # raise HTTPException(status_code=HTTP_403_FORBIDDEN,
            #                     detail="You don't have enough rights to perform this action")
            return status, payload
        elif status == 404:
            # raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Page not found")
            return status, payload
        else:
            # raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Something went wrong")
            return status, payload

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
