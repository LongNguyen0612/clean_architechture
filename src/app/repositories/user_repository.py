from abc import ABC, abstractmethod

from src.domain.user import User


class UserRepository(ABC):

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> User:
        pass

    @abstractmethod
    async def generate_id(self):
        pass
