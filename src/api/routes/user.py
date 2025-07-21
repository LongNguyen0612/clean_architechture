from fastapi import APIRouter, Depends, status, Body
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Any, List, Optional
import logging

from src.app.use_case import (
    CreateUserCommand,
    CreateUserUseCase,
    CreateUserResult
)
from src.depends import get_unit_of_work, get_redis_client
from src.api.error import ClientError, ServerError


logger = logging.getLogger(__name__)
router = APIRouter()

class CreateUserRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address of the new user")
    name: str = Field(..., min_length=1, max_length=100, description="Full name of the user")
    global_role: str = Field(..., description="Only global role is allowed to be assigned")
    

@router.post("/users", response_model=CreateUserResult, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    unit_of_work=Depends(get_unit_of_work),
    redis_client=Depends(get_redis_client)
):
    """
    Creates a new user in the system (Travel Hub team only).

    Logic Flow:
    1. Get user from payload
    2. Check if UserRepository.find_by_email() else return email existed
    3. Check if OrganizationRepository.find_by_id() else return organization not found
    4. Check if RoleRepository.find_by_name else return role not found
    5. Create new User
    6. Create Celery background task to send reset email
    7. Return response

    Required permission: user:write:create
    """
    # Create and execute the use case
    command = CreateUserCommand(
        email=body.email,
        name=body.name,
    )

    use_case = CreateUserUseCase(unit_of_work, redis_client)
    result = await use_case.execute(command)

    if result.is_err():
        error = result.value
        if error.code in ["user_already_exists"]:
            raise ClientError(base_error=error, status_code=status.HTTP_400_BAD_REQUEST)
        else:
            raise ServerError(base_error=error)

    created_user = result.value

    # Log the successful user creation
    logger.info(f"User created successfully: {created_user.id} ({created_user.email})")

    # Return the CreateUserResult directly
    return created_user