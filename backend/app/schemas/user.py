import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserBase, UserStatus
from app.models.mixin import TimeStampMixin


class UserRegister(BaseModel):
    username: str = Field(max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    username: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase, TimeStampMixin):
    id: uuid.UUID


class UserCreate(UserBase):
    hashed_password: str = Field(max_length=255)


class UserUpdate(BaseModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    status: UserStatus | None = None
