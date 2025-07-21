import uuid
import logging
from typing import Optional

from src.domain import User as UserORM
from src.app.repositories import UserRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class SQLUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger

    async def get_by_id(self, user_id: str) -> Optional[UserORM]:
        self.logger.debug(f"Repository operation: find_by_id(user_id='{user_id}')")

        result = await self.session.execute(
            select(UserORM).where(UserORM.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            self.logger.debug(f"Repository result: User found with id='{user_id}'")
        else:
            self.logger.debug(f"Repository result: No user found with id='{user_id}'")

        return user

    async def find_by_email(self, email: str) -> Optional[UserORM]:
        self.logger.debug(f"Repository operation: find_by_email(email='{email}')")

        result = await self.session.execute(
            select(UserORM).where(UserORM.email == email)
        )
        user = result.scalar_one_or_none()

        if user:
            self.logger.debug(f"Repository result: User found with id={user.id}, email='{email}'")
        else:
            self.logger.debug(f"Repository result: No user found with email='{email}'")

        return user

    async def generate_id(self) -> str:
        generated_id = str(uuid.uuid4())
        self.logger.debug(f"Repository operation: generate_id() => '{generated_id}'")
        return generated_id

    async def save(self, user_orm: UserORM) -> UserORM:
        # If the user doesn't have an ID yet, generate one
        if not user_orm.id:
            user_orm.id = await self.generate_id()
            self.logger.debug(f"Repository operation: save(new user) with id='{user_orm.id}', email='{user_orm.email}'")
        else:
            self.logger.debug(
                f"Repository operation: save(existing user) with id='{user_orm.id}', email='{user_orm.email}'")

        self.session.add(user_orm)
        await self.session.flush()

        self.logger.debug(f"Repository result: User saved successfully with id='{user_orm.id}'")
        return user_orm
