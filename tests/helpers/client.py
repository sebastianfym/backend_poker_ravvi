import logging
import asyncio
import aiohttp
import websockets
import json
import time
from urllib.parse import urlencode

from ravvi_poker.engine.events import Message, Command

log = logging.getLogger(__name__)

class Client:
    API_URL = 'http://localhost:8001'
    WS_URL = 'ws://localhost:8002'

    def __init__(self) -> None:
        self.device_token = None
        self.access_token = None
        self.user_id = None
        self.ws = None
        self.ws_task = None
        self.ws_lock = asyncio.Lock()
        self.ws_event = asyncio.Event()
        self.ws_event_type = None
        self.ws_log = []

    def api_url(self, path):
        return self.API_URL+path
    
    async def get_result(self, response):
        payload = None
        if response.ok:
            payload = await response.json()
        return response.status, payload
                    
    async def get(self, path, **params):
        async with aiohttp.ClientSession() as session:
            async with session.request('GET', self.api_url(path), params = params) as response:
               return await self.get_result(response)
            
    async def post(self, path, **params):
        async with aiohttp.ClientSession() as session:
            async with session.request('POST', self.api_url(path), json = params) as response:
               return await self.get_result(response)
            
    async def register(self):
        status, data = await self.post('/api/v1/auth/register')
        assert status == 200
        assert data
        assert 'device_token' in data
        assert 'access_token' in data
        assert 'user_id' in data
        self.device_token = data['device_token']
        self.access_token = data['access_token']
        self.user_id = data['user_id']
        log.debug('registered: user_id = %s', self.user_id)

    async def ws_connect(self):
        assert not self.ws
        params = urlencode(dict(access_token=self.access_token))
        uri = f"{self.WS_URL}/v1/ws?{params}"
        self.ws = await websockets.connect(uri)
        assert self.ws
        self.ws_task = asyncio.create_task(self.run_ws_recv())
        await asyncio.sleep(0.1)

    async def run_ws_recv(self):
        log.info("run_ws_recv ...")
        try:
            while True:
                msg = await self.ws.recv()
                kwargs = json.loads(msg)
                msg = Message(**kwargs)
                log.info("ws recv: %s", msg)
                async with self.ws_lock:
                    self.ws_log.append(msg)
                    msg_type = Message.Type.decode(msg.msg_type)
                    if self.ws_event_type==msg_type:
                        self.ws_event.set()

        except websockets.ConnectionClosed as e:
            log.info("run_ws_recv: closed: %s: %s", type(e), e)
        except asyncio.CancelledError:
            log.info("run_ws_recv: cancel")
        except Exception as e:
            log.error("run_ws_recv: error: %s, %s", type(e), e)
        log.info("run_ws_recv: end")

    async def ws_close(self):
        if not self.ws:
            return
        await self.ws.close()
        #if not self.ws_task.done():
        #    self.ws_task.cancel()
        await self.ws_task

    async def cmd_TABLE_JOIN(self, **kwargs):
        cmd = dict(cmd_type=11, **kwargs)
        cmd = json.dumps(cmd)
        log.info("cmd %s", cmd)
        ret = await self.ws.send(cmd)
        log.info("cmd %s", ret)

    def ws_response(self, event_type, timeout=2):
        return WS_Response(self, event_type, timeout)

class WS_Response:
    def __init__(self, client, event_type, timeout) -> None:
        self.client = client
        self.event_type = event_type
        self.timeout = timeout
        self.start_time = None
        self.stop_time = None

    async def __aenter__(self):
        async with self.client.ws_lock:
            self.client.ws_event.clear()
            self.client.ws_event_type = self.event_type
        self.start_time = time.monotonic_ns()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if exc_type:
            return
        await asyncio.wait_for(self.client.ws_event.wait(), self.timeout)
        self.stop_time = time.monotonic_ns()


    @property
    def time_ns(self):
        return self.stop_time-self.start_time

    @property
    def time_mcs(self):
        return self.time_ns/1e3

    @property
    def time_ms(self):
        return self.time_ns/1e6

    @property
    def time_s(self):
        return self.time_ns/1e9
