from src.app.services import UnitOfWork
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from src.adapter.repositories import (
    SQLUserRepository,

)

class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session: AsyncSession = session_factory()

    async def __aenter__(self):
        await self.session.__aenter__()
        # TODO: please provide SQLRepository here
        self.user_repository = SQLUserRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.__aexit__(exc_type, exc_val, exc_tb)
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
