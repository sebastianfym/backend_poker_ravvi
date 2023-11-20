from .adbi import DBI

class DBI_Txn:
    def __init__(self, db: DBI) -> None:
        self.dbi = db.dbi

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            await self.dbi.commit()
        else:
            await self.dbi.rollback()
        self.dbi = None