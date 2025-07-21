from abc import ABC, abstractmethod

from src.app.repositories import UserRepository


class UnitOfWork(ABC):
    # TODO: Provide repositories interface here
    user_repository: UserRepository

    @abstractmethod
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass
