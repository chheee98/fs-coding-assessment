import uuid
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, SQLModel, Relationship


from app.models.mixin import TimeStampMixin

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.todo import Todo

class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class UserBase(SQLModel):
    email: EmailStr | None = Field(
        default=None, max_length=255, unique=True, index=True, nullable=True
    )
    username: str = Field(max_length=64, unique=True, index=True, nullable=False)
    status: UserStatus = Field(default=UserStatus.ACTIVE, nullable=False)


class User(UserBase, TimeStampMixin, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False
    )
    hashed_password: str = Field(max_length=255, nullable=False)
    todos: list["Todo"] = Relationship(back_populates="user")
