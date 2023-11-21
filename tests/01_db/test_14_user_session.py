import pytest

from ravvi_poker.db.adbi import DBI


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_session(session):
    def check_row(row):
        assert row
        assert row.id == session.id
        assert row.uuid == session.uuid
        assert row.login_id == session.login_id
        assert row.created_ts
        assert row.closed_ts is None

    async with DBI() as db:
        row = await db.get_session(session.id)
        check_row(row)

        row = await db.get_session(uuid=session.uuid)
        check_row(row)


@pytest.mark.dependency(depends=["test_session"])
@pytest.mark.asyncio
async def test_session_constrains(session):
    with pytest.raises(DBI.ForeignKeyViolation):
        async with DBI() as db:
            # invalid login
            await db.create_session(-1)


@pytest.mark.dependency(depends=["test_session_constrains"])
@pytest.mark.asyncio
async def test_session_info(session):
    def check_row(row):
        assert row

    async with DBI() as db:
        row = await db.get_session_info(session.id)
        check_row(row)

        row = await db.get_session_info(uuid=session.uuid)
        check_row(row)
