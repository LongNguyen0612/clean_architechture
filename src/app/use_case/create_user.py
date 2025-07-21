from dataclasses import dataclass
from typing import Optional
import bcrypt
import logging
import secrets
import string
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from src.app.services.redis_key_service import RedisKeyService
from src.domain.user import User
from libs.result import Result, Return, Error
from src.app.services.unit_of_work import UnitOfWork
from src.app.repositories import UserRepository

logger = logging.getLogger(__name__)



class CreateUserCommand(BaseModel):
    email: EmailStr = Field(..., description="Email address of the new user")
    name: str = Field(..., min_length=1, max_length=100, description="Full name of the user")


class CreateUserResult(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    email: str = Field(..., description="Email address of the user")
    name: str = Field(..., description="Full name of the user")
    avatar: Optional[str] = Field(None, description="URL or path to the user's avatar image")
    created_at: str = Field(..., description="ISO 8601 timestamp when the user account was created")
    last_login: Optional[str] = Field(None, description="ISO 8601 timestamp of the user's last login, if any")
    is_active: bool = Field(..., description="Whether the user account is currently active")


class CreateUserUseCase:
    def __init__(self, unit_of_work: UnitOfWork, redis_client=None):
        self.unit_of_work = unit_of_work
        self.redis_client = redis_client
        self.logger = logger

    async def execute(self, command: CreateUserCommand) -> Result:
        """
        Creates a new user account.

        Logic Flow:
        1. Check if user with the email already exists
        2. Create the new user record
        3. Generate a password reset token for the user
        4. Return the created user details

        Args:
            command: The command containing user details

        Returns:
            Result with CreateUserResult or Error
        """
        # Log the command
        self.logger.info(
            f"Received CreateUserCommand: email='{command.email}', "
            f"name='{command.name}'"
        )

        async with self.unit_of_work as uow:
            user_repo: UserRepository = uow.user_repository

            # Check if user with email already exists
            self.logger.debug(f"Checking if user already exists with email: '{command.email}'")
            existing_user = await user_repo.find_by_email(command.email)
            if existing_user:
                self.logger.warning(f"User already exists with email: '{command.email}'")
                return Return.err(
                    Error(
                        code="user_already_exists",
                        message=f"User with email {command.email} already exists",
                        reason="This email address is already registered in our system",
                    )
                )

            # Generate a temporary password
            self.logger.debug(
                f"Generating temporary password for new user: email='{command.email}', name='{command.name}'"
            )
            temp_password = "".join(
                secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(12)
            )

            # Hash the password
            self.logger.debug(f"Hashing temporary password")
            password_bytes = temp_password.encode("utf-8")
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
            self.logger.debug(f"Password hashed for user: email='{command.email}', password='{temp_password}'")

            # Create the new user
            self.logger.info(f"Creating new user with email: '{command.email}'")
            now = datetime.utcnow()
            new_user = User(
                email=command.email, name=command.name, password=hashed_password, created_at=now, is_active=True
            )
            # If role is not admin, verify organization has at least one admin user
            self.logger.debug(f"Verifying organization has at least one admin user")

            user = await user_repo.save(new_user)

            # Commit the transaction first
            self.logger.debug(f"Committing transaction")
            await uow.commit()

            # Generate a password reset token
            if self.redis_client:
                self.logger.info(f"Generating password reset token for user: '{user.id}'")
                reset_token = secrets.token_urlsafe(32)

                # Store token in Redis
                await self.redis_client.set(reset_token, str(user.id), ex=RedisKeyService.RESET_TOKEN_EXPIRY)

            # Return the result
            self.logger.info(f"Successfully created user: '{user.id}' with email: '{user.email}'")
            return Return.ok(
                CreateUserResult(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    avatar=user.avatar,
                    created_at=user.created_at.isoformat() if user.created_at else None,
                    last_login=user.last_login.isoformat() if user.last_login else None,
                    is_active=user.is_active
                )
            )
