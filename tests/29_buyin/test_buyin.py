import pytest

from ravvi_poker.client.client import PokerClient


class TestBuyin:
    @pytest.mark.asyncio
    async def test_base(self):
        client = PokerClient()

        async with client:
            await client.auth_register()
            new_club = await client.create_club()
            new_table = await client.create_table(club_id=new_club.id, table_type="RG",
                                                  buyin_min=10, buyin_max=20, action_time=15,
                                                  blind_small=0.1, blind_big=0.2,
                                                  table_seats=2,
                                                  game_type="NLH", game_subtype="REGULAR")
