from typing import Annotated

from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends
from app.db.session import get_async_session
from app.repositories.todo_repository import TodoRepository
from app.services.todo_service import TodoService


def get_todo_service(session: AsyncSession = Depends(get_async_session)) -> TodoService:
    todo_repository = TodoRepository(session)
    return TodoService(todo_repository)

TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]