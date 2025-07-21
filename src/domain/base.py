from sqlmodel import SQLModel
import uuid


class BaseModel(SQLModel):
    """Base model for all domain models"""

    class Config:
        arbitrary_types_allowed = True


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())

