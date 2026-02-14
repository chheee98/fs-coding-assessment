from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_async_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


def get_user_service(session: AsyncSession = Depends(get_async_session)) -> UserService:
    user_repository = UserRepository(session)
    return UserService(user_repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
