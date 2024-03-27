import asyncio
import sys
import time
from multiprocessing import Pool, cpu_count

import pytest

from ravvi_poker.client.client import PokerClient

collected_data = []


@pytest.fixture(autouse=True)
def clear_collected_data():
    collected_data.clear()
    collected_data_client_1.clear()
    collected_data_client_2.clear()


class TestBuyInTableJoin:
    async def handler_collector(self, payload):
        collected_data.append(payload)

    @pytest.mark.asyncio
    async def test_not_enough_balance(self):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)
            await asyncio.sleep(3)

            assert collected_data == [
                # сообщение о недостатке денег на балансе
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 102,
                    "props": {"error_id": 400, "error_text": "Not enough balance"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [None, None],
                        "table_redirect_id": new_table.id,
                        "users": [],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]

    @pytest.mark.asyncio
    async def test_give_offer(self):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                # сообщение с оффером
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [client.user_id, None],
                        "table_redirect_id": new_table.id,
                        "users": [{'balance': None,
                                   'cards': [],
                                   'id': client.user_id,
                                   'image_id': None,
                                   'name': f"u{client.user_id}"}],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]

    @pytest.mark.asyncio
    async def test_correct_accept_offer(self):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                # сообщение о недостатке денег на балансе
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [client.user_id, None],
                        "table_redirect_id": new_table.id,
                        "users": [{'balance': None,
                                   'cards': [],
                                   'id': client.user_id,
                                   'image_id': None,
                                   'name': f"u{client.user_id}"}],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]
            collected_data.clear()

            await client.accept_offer(table_id=new_table.id, buyin_value=10)
            await asyncio.sleep(3)

            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 205,
                    "props": {"balance": 10, "user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]

            member_data = await client.get_detail_member_info(new_club.id)
            assert member_data.balance == 40

    @pytest.mark.asyncio
    @pytest.mark.parametrize("buyin_value", [5, 25])
    async def test_incorrect_accept_offer_balance_value(self, buyin_value: int):
        """
        На момент получения оффера денег на балансе достаточно. На момент отправки команды в ответ на оффер -
        баланса уже не достаточно.
        """
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                # сообщение о недостатке денег на балансе
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [client.user_id, None],
                        "table_redirect_id": new_table.id,
                        "users": [{'balance': None,
                                   'cards': [],
                                   'id': client.user_id,
                                   'image_id': None,
                                   'name': f"u{client.user_id}"}],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]
            collected_data.clear()

            await client.down_user_balance(new_club.id, -50, [
                {
                    "id": client.user_id,
                    "balance": 1000,
                    "balance_shared": None
                }
            ])
            await client.accept_offer(table_id=new_table.id, buyin_value=buyin_value)
            await asyncio.sleep(3)

            assert collected_data == [
                # сообщение что денег на балансе недостаточно
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 102,
                    "props": {"error_id": 400, "error_text": "Not enough balance"},
                    "table_id": new_table.id
                },
            ]
            collected_data.clear()

            await asyncio.sleep(70)

            assert collected_data == [
                # сообщение о выходе из-за стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 299,
                    "props": {"user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("buyin_value", [5, 25])
    async def test_incorrect_accept_offer_buyin_value(self, buyin_value):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                # сообщение о недостатке денег на балансе
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [client.user_id, None],
                        "table_redirect_id": new_table.id,
                        "users": [{'balance': None,
                                   'cards': [],
                                   'id': client.user_id,
                                   'image_id': None,
                                   'name': f"u{client.user_id}"}],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]
            collected_data.clear()

            await client.accept_offer(table_id=new_table.id, buyin_value=buyin_value)
            await asyncio.sleep(3)

            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 102,
                    "props": {"error_id": 400, "error_text": "Incorrect buyin value"},
                    "table_id": new_table.id
                },
            ]
            collected_data.clear()

            await asyncio.sleep(70)

            assert collected_data == [
                # сообщение о выходе из-за стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 299,
                    "props": {"user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]

    @pytest.mark.asyncio
    async def test_offer_timeout(self):
        """
        Проверить что если оффер просрочен, то участника выкинет из-за стола, а команда с байином будет проигнорирована
        """
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                # сообщение о недостатке денег на балансе
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [client.user_id, None],
                        "table_redirect_id": new_table.id,
                        "users": [{'balance': None,
                                   'cards': [],
                                   'id': client.user_id,
                                   'image_id': None,
                                   'name': f"u{client.user_id}"}],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]
            collected_data.clear()

            await asyncio.sleep(70)

            assert collected_data == [
                # сообщение о выходе из-за стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 299,
                    "props": {"user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]


class TestBuyInTakeSeat:
    async def handler_collector(self, payload):
        collected_data.append(payload)

    @pytest.mark.asyncio
    async def test_not_enough_balance(self):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)
            # ждем пока нас попытаются посадить, но придет отказ по причине недостатка баланса
            await asyncio.sleep(3)
            collected_data.clear()

            await client.take_seat(table_id=new_table.id, seat_idx=0)
            await asyncio.sleep(3)

            assert collected_data == [
                # сообщение о недостатке денег на балансе
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 102,
                    "props": {"error_id": 400, "error_text": "Not enough balance"},
                    "table_id": new_table.id
                },
            ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("wait_method", ["wait_timeout", "decline_offer"])
    async def test_give_offer(self, wait_method):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)

            if wait_method == "wait_timeout":
                # ждем пока оффер просрочится
                await asyncio.sleep(70)
            elif wait_method == "decline_offer":
                # отклоняем оффер
                await client.decline_offer(table_id=new_table.id)
                await asyncio.sleep(3)
            else:
                return
            collected_data.clear()

            await client.take_seat(table_id=new_table.id, seat_idx=0)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с информацией, что нас посадили за стол
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client.user_id,
                                 'image_id': None,
                                 'name': f"u{client.user_id}"},
                    }
                }
            ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("wait_method", ["wait_timeout", "decline_offer"])
    async def test_correct_accept_offer(self, wait_method: str):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)

            if wait_method == "wait_timeout":
                # ждем пока оффер просрочится
                await asyncio.sleep(70)
            elif wait_method == "decline_offer":
                # отклоняем оффер
                await client.decline_offer(table_id=new_table.id)
                await asyncio.sleep(3)
            else:
                return
            collected_data.clear()

            await client.take_seat(table_id=new_table.id, seat_idx=0)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client.user_id,
                                 'image_id': None,
                                 'name': f"u{client.user_id}"},
                    }
                }
            ]
            collected_data.clear()

            await client.accept_offer(table_id=new_table.id, buyin_value=10)
            await asyncio.sleep(3)

            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 205,
                    "props": {"balance": 10, "user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]

            member_data = await client.get_detail_member_info(new_club.id)
            assert member_data.balance == 40

    @pytest.mark.asyncio
    @pytest.mark.parametrize("wait_method, buyin_value", [
        ["wait_timeout", 5],
        ["wait_timeout", 25],
        ["decline_offer", 5],
        ["decline_offer", 25]
    ])
    async def test_incorrect_accept_offer_balance_value(self, wait_method: str, buyin_value: int):
        """
        На момент получения оффера денег на балансе достаточно. На момент отправки команды в ответ на оффер -
        баланса уже не достаточно.
        """
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)

            if wait_method == "wait_timeout":
                # ждем пока оффер просрочится
                await asyncio.sleep(70)
            elif wait_method == "decline_offer":
                # отклоняем оффер
                await client.decline_offer(table_id=new_table.id)
                await asyncio.sleep(3)
            else:
                return
            collected_data.clear()

            await client.take_seat(table_id=new_table.id, seat_idx=0)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client.user_id,
                                 'image_id': None,
                                 'name': f"u{client.user_id}"},
                    }
                }
            ]
            collected_data.clear()

            await client.down_user_balance(new_club.id, -50, [
                {
                    "id": client.user_id,
                    "balance": 1000,
                    "balance_shared": None
                }
            ])
            await client.accept_offer(table_id=new_table.id, buyin_value=buyin_value)
            await asyncio.sleep(3)

            assert collected_data == [
                # сообщение что денег на балансе недостаточно
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 102,
                    "props": {"error_id": 400, "error_text": "Not enough balance"},
                    "table_id": new_table.id
                },
            ]
            collected_data.clear()

            await asyncio.sleep(70)

            assert collected_data == [
                # сообщение о выходе из-за стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 299,
                    "props": {"user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("wait_method, buyin_value", [
        ["wait_timeout", 5],
        ["wait_timeout", 25],
        ["decline_offer", 5],
        ["decline_offer", 25]
    ])
    async def test_incorrect_accept_offer_buyin_value(self, wait_method, buyin_value):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)

            if wait_method == "wait_timeout":
                # ждем пока оффер просрочится
                await asyncio.sleep(70)
            elif wait_method == "decline_offer":
                # отклоняем оффер
                await client.decline_offer(table_id=new_table.id)
                await asyncio.sleep(3)
            else:
                return
            collected_data.clear()

            await client.take_seat(table_id=new_table.id, seat_idx=0)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client.user_id,
                                 'image_id': None,
                                 'name': f"u{client.user_id}"},
                    }
                }
            ]
            collected_data.clear()

            await client.accept_offer(table_id=new_table.id, buyin_value=buyin_value)
            await asyncio.sleep(3)

            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 102,
                    "props": {"error_id": 400, "error_text": "Incorrect buyin value"},
                    "table_id": new_table.id
                },
            ]
            collected_data.clear()

            await asyncio.sleep(70)

            assert collected_data == [
                # сообщение о выходе из-за стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 299,
                    "props": {"user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("wait_method", ["wait_timeout", "decline_offer"])
    async def test_offer_timeout(self, wait_method):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector)

            if wait_method == "wait_timeout":
                # ждем пока оффер просрочится
                await asyncio.sleep(70)
            elif wait_method == "decline_offer":
                # отклоняем оффер
                await client.decline_offer(table_id=new_table.id)
                await asyncio.sleep(3)
            else:
                return
            collected_data.clear()

            await client.take_seat(table_id=new_table.id, seat_idx=0)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data[0]["props"]["closed_at"] < time.time() + 60
            collected_data[0]["props"]["closed_at"] = 0
            assert collected_data == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client.user_id,
                                 'image_id': None,
                                 'name': f"u{client.user_id}"},
                    }
                }
            ]
            collected_data.clear()

            await asyncio.sleep(70)

            assert collected_data == [
                # сообщение о выходе из-за стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 299,
                    "props": {"user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]


collected_data_client_1 = []
collected_data_client_2 = []


class TestReplenishBalance:
    async def handler_collector_client_1(self, payload):
        collected_data_client_1.append(payload)

    async def handler_collector_client_2(self, payload):
        collected_data_client_2.append(payload)

    @pytest.mark.asyncio
    async def test_replenish_balance_not_game(self):
        """
        Проверяем что баланс пополнится. Аккаунт уже за столом. Игра не идет
        """
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            await client.update_club(club_id=new_club.id, automatic_confirmation=True)

            # пополняем баланс клуба
            await client.up_club_balance(new_club.id, 1000)
            await client.up_user_balance(new_club.id, 50,
                                         [
                                             {
                                                 "id": client.user_id,
                                                 "balance": 1000,
                                                 "balance_shared": None
                                             }
                                         ]
                                         )

            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client.create_table(club_id=new_club.id, **table_params,
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client.join_table(new_table.id, new_club.id, True, self.handler_collector_client_1)
            await asyncio.sleep(3)

            # проверим что время в оффере верное и заменим его на 0
            assert collected_data_client_1[0]["props"]["closed_at"] < time.time() + 60
            collected_data_client_1[0]["props"]["closed_at"] = 0
            assert collected_data_client_1 == [
                # сообщение с оффером
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с параметрами стола
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [client.user_id, None],
                        "table_redirect_id": new_table.id,
                        "users": [{'balance': None,
                                   'cards': [],
                                   'id': client.user_id,
                                   'image_id': None,
                                   'name': f"u{client.user_id}"}],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]
            collected_data_client_1.clear()

            await client.accept_offer(table_id=new_table.id, buyin_value=10)
            await asyncio.sleep(3)

            assert collected_data_client_1 == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 205,
                    "props": {"balance": 10, "user_id": client.user_id},
                    "table_id": new_table.id
                }
            ]
            collected_data_client_1.clear()

            member_data = await client.get_detail_member_info(new_club.id)
            assert member_data.balance == 40

            await client.request_offer(new_table.id)
            await asyncio.sleep(3)

            assert collected_data_client_1[0]["props"]["closed_at"] < time.time() + 60
            collected_data_client_1[0]["props"]["closed_at"] = 0
            assert collected_data_client_1 == [
                # сообщение с оффером
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 40, "buyin_range": [0.2, 10.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
            ]
            collected_data_client_1.clear()

            await client.accept_offer(table_id=new_table.id, buyin_value=0.2)
            await asyncio.sleep(3)

            # проверяем что деньги не спишутся сразу
            member_data = await client.get_detail_member_info(new_club.id)
            assert member_data.balance == 40

    # @pytest.mark.asyncio
    # async def test_replenish_balance_in_game(self):
    #     """
    #     Проверяем что баланс не пополнится, пока игра не закончится. Аккаунт уже за столом и идет игра.
    #     """
    #     client1, client2 = PokerClient(), PokerClient()
    #
    #     async with client1, client2:
    #         await client1.auth_register()
    #         await client2.auth_register()
    #
    #         # создаем клуб, вступаем и подтверждаем заявку
    #         new_club = await client1.create_club()
    #         await client2.send_req_join_in_club(new_club.id)
    #         await client1.approve_req_to_join(new_club.id, client2.user_id)
    #
    #         # пополняем баланс клуба
    #         await client1.up_club_balance(new_club.id, 1000)
    #         await client1.up_user_balance(new_club.id, 100,
    #                                       [
    #                                           {
    #                                               "id": client1.user_id,
    #                                               "balance": 1000,
    #                                               "balance_shared": None
    #                                           },
    #                                           {
    #                                               "id": client2.user_id,
    #                                               "balance": 1000,
    #                                               "balance_shared": None
    #                                           }
    #                                       ]
    #                                       )
    #
    #         # создаем стол
    #         table_params = {
    #             "blind_small": 0.1,
    #             "blind_big": 0.2,
    #             "game_type": "NLH",
    #             "game_subtype": "REGULAR",
    #             "table_type": "RG"
    #         }
    #         new_table = await client1.create_table(club_id=new_club.id, **table_params,
    #                                                buyin_min=10, buyin_max=20, action_time=15,
    #                                                table_seats=2)
    #         # дождемся старта стола
    #         await asyncio.sleep(3)
    #
    #         await client1.join_table(new_table.id, new_club.id, True, self.handler_collector_client_1)
    #         await client2.join_table(new_table.id, new_club.id, True, self.handler_collector_client_2)
    #         await asyncio.sleep(3)
    #
    #         await client1.accept_offer(new_table.id, buyin_value=10)
    #         await client2.accept_offer(new_table.id, buyin_value=10)
    #         await asyncio.sleep(3)
    #         collected_data_client_1.clear()
    #         collected_data_client_2.clear()
    #
    #         await asyncio.sleep(10)
    #
    #         await client1.request_offer(new_table.id)
    #         await asyncio.sleep(15)
    #
    #         print([f"{msg}" + "\n" for msg in collected_data_client_1 if msg["msg_type"] not in [301, 203, 204, 304]])
    #         print(collected_data_client_2)
    #         raise ValueError


class TestBuyInTwoClientsForAccount:
    async def handler_collector_client_1(self, payload):
        collected_data_client_1.append(payload)

    async def handler_collector_client_2(self, payload):
        collected_data_client_2.append(payload)

    @pytest.mark.asyncio
    async def test_two_clients_one_offer_take_seat(self):
        """
        Проверяем что если один аккаунт находится за двумя устройствами, то оффер получит только то устройство,
        которое инициировало take_seat (оба клиента зашли как зрители)
        """
        client1, client2 = PokerClient(), PokerClient()

        async with client1, client2:
            await client1.auth_register()
            await client1.password_update(None, "12345678")
            await client2.login_with_username_and_password(f"{client1.user_id}", "12345678")

            new_club = await client1.create_club()

            # пополняем баланс клуба
            await client1.up_club_balance(new_club.id, 1000)
            await client1.up_user_balance(new_club.id, 50,
                                          [
                                              {
                                                  "id": client1.user_id,
                                                  "balance": 1000,
                                                  "balance_shared": None
                                              }
                                          ]
                                          )

            # создаем стол
            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client1.create_table(club_id=new_club.id, **table_params,
                                                   buyin_min=10, buyin_max=20, action_time=15,
                                                   table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client1.join_table(new_table.id, new_club.id, False, self.handler_collector_client_1)
            await client2.join_table(new_table.id, new_club.id, False, self.handler_collector_client_2)
            await asyncio.sleep(3)

            # проверяем что у обоих аккаунтов только приветственное сообщение
            assert collected_data_client_1 == collected_data_client_2 == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [None, None],
                        "table_redirect_id": new_table.id,
                        "users": [],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]
            collected_data_client_1.clear()
            collected_data_client_2.clear()

            await client1.take_seat(new_table.id, 0)
            await asyncio.sleep(3)

            assert collected_data_client_1[0]["props"]["closed_at"] < time.time() + 60
            collected_data_client_1[0]["props"]["closed_at"] = 0
            assert collected_data_client_1 == [
                # предложение оффера
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с информацией, что нас посадили за стол
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client1.user_id,
                                 'image_id': None,
                                 'name': f"u{client1.user_id}"},
                    }
                }
            ]
            assert collected_data_client_2 == [
                # сообщение с информацией, что нас посадили за стол
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client2.user_id,
                                 'image_id': None,
                                 'name': f"u{client2.user_id}"},
                    }
                }
            ]

    @pytest.mark.asyncio
    async def test_two_clients_two_offer_take_seat(self):
        """
        Проверяем что если один аккаунт находится за двумя устройствами, то оффер получит только то устройство,
        которое инициировало take_seat (оба клиента зашли как зрители). После того как второе устройство запросит оффер,
        то оно пропадет с первого устройства
        """
        client1, client2 = PokerClient(), PokerClient()

        async with client1, client2:
            await client1.auth_register()
            await client1.password_update(None, "12345678")
            await client2.login_with_username_and_password(f"{client1.user_id}", "12345678")

            new_club = await client1.create_club()

            # пополняем баланс клуба
            await client1.up_club_balance(new_club.id, 1000)
            await client1.up_user_balance(new_club.id, 50,
                                          [
                                              {
                                                  "id": client1.user_id,
                                                  "balance": 1000,
                                                  "balance_shared": None
                                              }
                                          ]
                                          )

            # создаем стол
            table_params = {
                "blind_small": 0.1,
                "blind_big": 0.2,
                "game_type": "NLH",
                "game_subtype": "REGULAR",
                "table_type": "RG"
            }
            new_table = await client1.create_table(club_id=new_club.id, **table_params,
                                                   buyin_min=10, buyin_max=20, action_time=15,
                                                   table_seats=2)
            # дождемся старта стола
            await asyncio.sleep(3)

            await client1.join_table(new_table.id, new_club.id, False, self.handler_collector_client_1)
            await client2.join_table(new_table.id, new_club.id, False, self.handler_collector_client_2)
            await asyncio.sleep(3)

            # проверяем что у обоих аккаунтов только приветственное сообщение
            assert collected_data_client_1 == collected_data_client_2 == [
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 101,
                    "table_id": new_table.id,
                    "props": table_params | {
                        "captcha": False,
                        "ev_chop": False,
                        "game": None,
                        "player_move": None,
                        "seats": [None, None],
                        "table_redirect_id": new_table.id,
                        "users": [],
                        "view_during_move": False,
                        'table_name': None
                    }
                }
            ]
            collected_data_client_1.clear()
            collected_data_client_2.clear()

            await client1.take_seat(new_table.id, 0)
            await asyncio.sleep(3)

            assert collected_data_client_1[0]["props"]["closed_at"] < time.time() + 60
            collected_data_client_1[0]["props"]["closed_at"] = 0
            assert collected_data_client_1 == [
                # предложение оффера
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # сообщение с информацией, что нас посадили за стол
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client1.user_id,
                                 'image_id': None,
                                 'name': f"u{client1.user_id}"},
                    }
                }
            ]
            assert collected_data_client_2 == [
                # сообщение с информацией, что нас посадили за стол
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 201,
                    "table_id": new_table.id,
                    "props": {
                        "seat_id": 0,
                        "user": {'balance': None,
                                 'id': client2.user_id,
                                 'image_id': None,
                                 'name': f"u{client2.user_id}"},
                    }
                }
            ]
            collected_data_client_1.clear()
            collected_data_client_2.clear()

            await asyncio.sleep(3)
            await client2.request_offer(new_table.id)
            await asyncio.sleep(3)

            assert collected_data_client_1 == [
                # сообщение - оффер более не действителен
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
            ]
            assert collected_data_client_2[1]["props"]["closed_at"] < time.time() + 60
            collected_data_client_2[1]["props"]["closed_at"] = 0
            assert collected_data_client_2 == [
                # сообщение - оффер более не действителен
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
                # предложение оффера
                {
                    "client_id": None,
                    "cmd_id": None,
                    "game_id": None,
                    "msg_type": 103,
                    "props": {"balance": 50, "buyin_range": [10.0, 20.0], "closed_at": 0, "offer_type": "buyin"},
                    "table_id": new_table.id
                },
            ]


if __name__ == "__main__":
    test_funcs = []
    for test_class in [obj for obj in dir() if "Test" in obj]:
        for test_func in [obj for obj in dir(locals()[test_class]) if obj[:4] == "test"]:
            test_funcs.append([f"tests/29_buyin/test_buyin.py::{test_class}::{test_func}", "-rN", "--disable-warnings"])

    with Pool(processes=cpu_count()) as pool:
        pool.map(pytest.main, test_funcs)
