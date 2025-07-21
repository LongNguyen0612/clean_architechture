from sqlmodel import Field
from .base import BaseModel, generate_uuid
from datetime import datetime


class User(BaseModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    email: str =  Field(max_length=255)
    name: str =  Field(max_length=255)
    password: str =  Field(max_length=255)
    avatar: str =  Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
