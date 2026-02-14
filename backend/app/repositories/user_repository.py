import uuid

from pydantic import EmailStr
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        user = await self.session.get(User, user_id)
        return user

    async def get_user_by_email(self, email: EmailStr) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.session.exec(statement)
        return result.first()

    async def get_user_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        result = await self.session.exec(statement)
        return result.first()

    async def get_users(self) -> list[User]:
        statement = select(User)
        result = await self.session.exec(statement)
        return result.all()

    async def register_user(self, user_in: UserCreate) -> User:
        user = User(**user_in.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user(self, user_id: uuid.UUID, user_in: UserCreate) -> User | None:
        user = await self.get_user(user_id)
        if not user:
            return None
        user_data = user_in.model_dump(exclude_unset=True)
        for key, value in user_data.items():
            setattr(user, key, value)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
