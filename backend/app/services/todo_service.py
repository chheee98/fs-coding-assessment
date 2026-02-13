import uuid
import math

from fastapi import HTTPException, status
from app.models.todo import Todo, Priority, TodoStatus
from app.repositories.todo_repository import TodoRepository
from app.schemas.todo import (
    TodoCreate,
    TodoRead,
    TodoPaginatedResponse,
    TodoReadList,
    TodoUpdate, TodoStats,
)


class TodoService:
    def __init__(self, todo_repository: TodoRepository):
        self.todo_repository = todo_repository

    async def create_todo(self, todo_in: TodoCreate, user_id: uuid.UUID) -> TodoRead:
        todo = Todo(
            **todo_in.model_dump(),
            user_id=user_id,
        )
        todo = await self.todo_repository.create(todo)
        return TodoRead.model_validate(todo)

    async def get_todos(
        self,
        current_user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        priority: Priority = None,
        completed: bool | None = None,
        search: str | None = None,
    ) -> TodoPaginatedResponse:
        todos, total = await self.todo_repository.get_all(
            page=page,
            page_size=page_size,
            priority=priority,
            completed=completed,
            search=search,
        )

        items = []
        for todo in todos:
            item = TodoReadList.model_validate(todo)
            if todo.user_id != current_user_id:
                item.description = None

            items.append(item)

        return TodoPaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_todo(
        self, todo_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> TodoRead:
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)
        return TodoRead.model_validate(todo)

    async def update_todo(
        self,
        todo_id: uuid.UUID,
        todo_in: TodoUpdate,
        current_user_id: uuid.UUID,
    ):
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)

        update_data = todo_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(todo, key, value)

        todo = await self.todo_repository.update(todo)
        return TodoRead.model_validate(todo)

    async def delete_todo(self, todo_id: uuid.UUID, current_user_id: uuid.UUID):
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)
        await self.todo_repository.delete(todo)

    async def toggle_complete(self, todo_id: uuid.UUID, current_user_id: uuid.UUID):
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)

        todo.status = (
            TodoStatus.COMPLETED
            if todo.status != TodoStatus.COMPLETED
            else TodoStatus.NOT_STARTED
        )
        await self.todo_repository.update(todo)
        return TodoRead.model_validate(todo)

    async def get_statistics(self, user_id: uuid.UUID) -> TodoStats:
        overall_statistics_row = await self.todo_repository.get_overall_statistics(
            user_id
        )
        statistics_by_priority = await self.todo_repository.get_statistics_by_priority(
            user_id
        )

        return TodoStats(
            total=overall_statistics_row.total,
            completed=overall_statistics_row.complete,
            pending=overall_statistics_row.pending,
            by_priority={
                row.priority: row.count
                for row in statistics_by_priority
            },
        )

    async def _get_todo_or_404(self, todo_id: uuid.UUID) -> Todo:
        """Get a todo by ID or raise 404."""
        todo = await self.todo_repository.get_by_id(todo_id)
        if not todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found",
            )
        return todo

    @staticmethod
    def _check_owner(todo: Todo, current_user_id: uuid.UUID) -> None:
        if todo.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this todo",
            )
